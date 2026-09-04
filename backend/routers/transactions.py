import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import AuditLog, Transaction
from backend.schemas import SeedResponse, TransactionListResponse, TransactionSchema
from data.sample.generator import generate_synthetic_transactions
from ai.classifier import Classifier
from ai.scorer import Scorer
from ai.strategy_generator import StrategyGenerator
from ai.policy_gate import PolicyGate, PlaybookProposal, TransactionContext

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])

classifier = Classifier()
scorer = Scorer()
strategy_gen = StrategyGenerator()
policy_gate = PolicyGate()


@router.post("/seed", response_model=SeedResponse)
def seed_transactions(db: Session = Depends(get_db)):
    """
    Generate and seed the ~600 synthetic transaction records (idempotent, fixed seed 42).
    """
    records = generate_synthetic_transactions(seed=42, count=600)

    # Clear existing transactions and audit logs for clean reproducible state
    db.query(AuditLog).delete()
    db.query(Transaction).delete()
    db.commit()

    db_records = []
    for r in records:
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

    return SeedResponse(
        status="success",
        count=len(db_records),
        seed=42,
        message=f"Successfully seeded {len(db_records)} synthetic failed transactions with seed 42.",
    )


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    root_cause: Optional[str] = Query(None),
    segment: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    fraud_flag: Optional[bool] = Query(None),
    edge_case_only: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List transactions with filtering by root_cause, customer segment, action, fraud flag, search.
    """
    query = db.query(Transaction)

    if root_cause:
        query = query.filter(Transaction.root_cause == root_cause)
    if segment:
        query = query.filter(Transaction.customer_segment == segment)
    if action:
        query = query.filter(Transaction.final_action == action)
    if fraud_flag is not None:
        query = query.filter(Transaction.fraud_flag == fraud_flag)
    if edge_case_only:
        query = query.filter(Transaction.edge_case_tag.isnot(None))
    if search:
        s = f"%{search}%"
        query = query.filter(
            (Transaction.transaction_id.ilike(s))
            | (Transaction.customer_id.ilike(s))
            | (Transaction.decline_message.ilike(s))
            | (Transaction.gateway.ilike(s))
        )

    total = query.count()
    items = query.order_by(Transaction.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()

    tx_schemas = [TransactionSchema.model_validate(t.to_dict()) for t in items]

    return TransactionListResponse(
        total=total,
        page=page,
        page_size=page_size,
        transactions=tx_schemas,
    )


@router.get("/{transaction_id}", response_model=TransactionSchema)
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    """
    Retrieve full transaction details including all 5 pipeline decision traces.
    """
    tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")

    return TransactionSchema.model_validate(tx.to_dict())


@router.post("/{transaction_id}/analyze", response_model=TransactionSchema)
def analyze_transaction(transaction_id: str, db: Session = Depends(get_db)):
    """
    Run pipeline steps 1-4 for a single transaction (Classifier -> Scorer -> Strategy -> Policy Gate).
    """
    tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")

    # Step 1: Classifier
    root_cause, root_rationale = classifier.classify(tx.decline_code, tx.decline_message)

    # Step 2: Scorer
    effective_root = "SUSPECTED_FRAUD" if tx.fraud_flag else root_cause
    score, factors = scorer.score(effective_root, tx.customer_segment, tx.previous_retry_count, tx.is_subscription)

    # Step 3: Strategy Generator (LLM)
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

    # Step 4: Policy Gate
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
        customer_retries_today=0,
        edge_case_tag=tx.edge_case_tag,
    )
    approved_proposal, verdict, overrides = policy_gate.evaluate(tx_ctx, proposed_proposal)

    # Persist in DB
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

    # Create AuditLog entry
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
    db.add(audit_entry)
    db.commit()
    db.refresh(tx)

    return TransactionSchema.model_validate(tx.to_dict())
