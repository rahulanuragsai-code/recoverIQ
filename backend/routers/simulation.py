import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import AuditLog, SimulationSummary, Transaction
from backend.schemas import SimulationMetricsResponse
from data.sample.generator import generate_synthetic_transactions
from ai.classifier import Classifier
from ai.scorer import Scorer
from ai.strategy_generator import StrategyGenerator
from ai.policy_gate import PolicyGate, PlaybookProposal, TransactionContext
from ai.simulator import Simulator

router = APIRouter(prefix="/api/simulate", tags=["Simulation"])

classifier = Classifier()
scorer = Scorer()
strategy_gen = StrategyGenerator()
policy_gate = PolicyGate()
simulator = Simulator(seed=42)


@router.post("/batch", response_model=SimulationMetricsResponse)
def run_batch_simulation(db: Session = Depends(get_db)):
    """
    Run pipeline steps 1-5 for the whole dataset + baseline comparison.
    Persists audit log entries per transaction and records benchmark KPIs.
    """
    transactions = db.query(Transaction).all()

    # If database is empty, auto-seed with 600 records first
    if not transactions:
        raw_records = generate_synthetic_transactions(seed=42, count=600)
        db_records = []
        for r in raw_records:
            tx = Transaction(
                transaction_id=r["transaction_id"],
                customer_id=r["customer_id"],
                customer_segment=r["customer_segment"],
                amount=r["amount"],
                currency=r["currency"],
                gateway=r["gateway"],
                decline_code=r["decline_code"],
                decline_message=r["decline_message"],
                timestamp=r["timestamp"],
                is_subscription=r["is_subscription"],
                previous_retry_count=r["previous_retry_count"],
                fraud_flag=r["fraud_flag"],
                is_synthetic=True,
                edge_case_tag=r.get("edge_case_tag"),
            )
            db_records.append(tx)
        db.add_all(db_records)
        db.commit()
        transactions = db.query(Transaction).all()

    # Clear previous audit logs for fresh run
    db.query(AuditLog).delete()
    db.commit()

    # Track customer velocity (retries assigned today) across batch
    customer_retries_today = defaultdict(int)

    items_to_simulate: List[Dict[str, Any]] = []
    audit_entries: List[AuditLog] = []

    for tx in transactions:
        # Step 1: Classifier
        root_cause, root_rationale = classifier.classify(tx.decline_code, tx.decline_message)

        # Step 2: Scorer
        effective_root = "SUSPECTED_FRAUD" if tx.fraud_flag else root_cause
        score, factors = scorer.score(effective_root, tx.customer_segment, tx.previous_retry_count, tx.is_subscription)

        # Step 3: Strategy Generator
        llm_context = {
            "transaction_id": tx.transaction_id,
            "root_cause": root_cause,
            "recoverability_score": score,
            "factors": factors,
            "customer_segment": tx.customer_segment,
            "is_subscription": tx.is_subscription,
            "previous_retry_count": tx.previous_retry_count,
            "fraud_flag": tx.fraud_flag,
            "edge_case_tag": tx.edge_case_tag,
        }
        proposed_dict = strategy_gen.generate_strategy(llm_context)
        proposed_proposal = PlaybookProposal(**proposed_dict)

        # Step 4: Policy Gate with dynamic customer velocity tracking
        tx_ctx = TransactionContext(
            transaction_id=tx.transaction_id,
            customer_id=tx.customer_id,
            customer_segment=tx.customer_segment,
            amount=tx.amount,
            decline_code=tx.decline_code,
            decline_message=tx.decline_message,
            previous_retry_count=tx.previous_retry_count,
            fraud_flag=tx.fraud_flag,
            is_subscription=tx.is_subscription,
            customer_retries_today=customer_retries_today[tx.customer_id],
            edge_case_tag=tx.edge_case_tag,
        )

        approved_proposal, verdict, overrides = policy_gate.evaluate(tx_ctx, proposed_proposal)

        # Update customer velocity count if retry authorized
        if approved_proposal.action in ["retry_now", "retry_scheduled"]:
            customer_retries_today[tx.customer_id] += approved_proposal.max_retries

        # Update transaction in DB
        tx.root_cause = root_cause
        tx.root_cause_rationale = root_rationale
        tx.recoverability_score = score
        tx.score_factors = json.dumps(factors)
        tx.proposed_action = proposed_proposal.action
        tx.proposed_playbook = json.dumps(proposed_proposal.to_dict())
        tx.policy_gate_verdict = verdict
        tx.policy_overrides = json.dumps(overrides)
        tx.final_action = approved_proposal.action
        tx.final_playbook = json.dumps(approved_proposal.to_dict())
        tx.analyzed_at = datetime.now(timezone.utc)

        # Create AuditLog record
        audit_entry = AuditLog(
            transaction_id=tx.transaction_id,
            customer_id=tx.customer_id,
            proposed_action=proposed_proposal.action,
            proposed_playbook=json.dumps(proposed_proposal.to_dict()),
            policy_verdict=verdict,
            rules_fired=json.dumps([o["rule"] for o in overrides]),
            override_reasons=json.dumps([o["reason"] for o in overrides]),
            final_action=approved_proposal.action,
            final_playbook=json.dumps(approved_proposal.to_dict()),
            created_at=datetime.now(timezone.utc),
        )
        audit_entries.append(audit_entry)

        items_to_simulate.append({
            "transaction": tx.to_dict(),
            "approved_playbook": approved_proposal.to_dict(),
            "recoverability_score": score,
            "policy_gate_verdict": verdict,
        })

    # Bulk insert audit entries
    db.add_all(audit_entries)
    db.commit()

    # Step 5: Simulator + Baseline Comparator
    simulated_txs, summary = simulator.simulate_batch(items_to_simulate)

    # Persist simulation outcomes back into transactions table
    sim_map = {t["transaction_id"]: t for t in simulated_txs}
    for tx in transactions:
        res = sim_map.get(tx.transaction_id)
        if res:
            tx.simulated_outcome_ai = res["simulated_outcome_ai"]
            tx.simulated_retries_ai = res["simulated_retries_ai"]
            tx.simulated_outcome_baseline = res["simulated_outcome_baseline"]
            tx.simulated_retries_baseline = res["simulated_retries_baseline"]
            tx.false_retry_avoided = res["false_retry_avoided"]

    # Persist SimulationSummary
    sim_record = SimulationSummary(
        seed=summary["seed"],
        total_transactions=summary["total_transactions"],
        amount_at_risk=summary["amount_at_risk"],
        amount_recovered_ai=summary["amount_recovered_ai"],
        amount_recovered_baseline=summary["amount_recovered_baseline"],
        recovery_rate_ai=summary["recovery_rate_ai"],
        recovery_rate_baseline=summary["recovery_rate_baseline"],
        recovery_rate_uplift_pct=summary["recovery_rate_uplift_pct"],
        false_retries_avoided=summary["false_retries_avoided"],
        policy_overrides_count=summary["policy_overrides_count"],
        simulated_at=datetime.now(timezone.utc),
    )
    db.add(sim_record)
    db.commit()

    return SimulationMetricsResponse(
        seed=summary["seed"],
        total_transactions=summary["total_transactions"],
        amount_at_risk=summary["amount_at_risk"],
        amount_recovered_ai=summary["amount_recovered_ai"],
        amount_recovered_baseline=summary["amount_recovered_baseline"],
        recovery_rate_ai=summary["recovery_rate_ai"],
        recovery_rate_baseline=summary["recovery_rate_baseline"],
        recovery_rate_uplift_pct=summary["recovery_rate_uplift_pct"],
        false_retries_avoided=summary["false_retries_avoided"],
        policy_overrides_count=summary["policy_overrides_count"],
        simulated_at=sim_record.simulated_at.isoformat(),
        root_cause_breakdown=summary["root_cause_breakdown"],
        action_breakdown=summary["action_breakdown"],
    )
