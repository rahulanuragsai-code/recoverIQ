"""
Tests for Seeded Edge Cases in RecoverIQ.
Verifies the system behavior on tricky real-world payment edge cases.
"""

import pytest
from ai.classifier import Classifier
from ai.scorer import Scorer
from ai.strategy_generator import StrategyGenerator
from ai.policy_gate import PolicyGate, PlaybookProposal, TransactionContext
from ai.simulator import Simulator


def test_edge_case_1_fraud_camouflage():
    """
    EDGE CASE 1:
    Decline message says: 'Transaction cannot be processed: balance check failed (code 51)'
    which looks deceptively like an insufficient funds error.
    However, the transaction has fraud_flag=True.
    The system must:
    1. Classify the error
    2. Score recoverability as 0.0 (fraud)
    3. LLM might propose retry
    4. Policy Gate strictly overrides to escalate_human and 0 retries
    5. Baseline would have blindly retried 3 times; AI avoids 3 false retries.
    """
    classifier = Classifier()
    scorer = Scorer()
    strategy_gen = StrategyGenerator()
    policy_gate = PolicyGate()
    simulator = Simulator(seed=42)

    raw_tx = {
        "transaction_id": "tx_edge_fraud_001",
        "customer_id": "cust_edge_9901",
        "customer_segment": "regular",
        "amount": 18500.0,
        "decline_code": "ISSUER_DECLINE",
        "decline_message": "Transaction cannot be processed: balance check failed (code 51)",
        "previous_retry_count": 0,
        "fraud_flag": True,
        "is_subscription": False,
        "edge_case_tag": "fraud_camouflage",
    }

    # Step 1: Classifier
    root_cause, rationale = classifier.classify(raw_tx["decline_code"], raw_tx["decline_message"])
    assert root_cause in ["INSUFFICIENT_FUNDS", "ISSUER_DECLINE", "SUSPECTED_FRAUD"]

    # Step 2: Scorer - fraud flag forces 0.0 score
    if raw_tx["fraud_flag"]:
        score, factors = scorer.score("SUSPECTED_FRAUD", raw_tx["customer_segment"], 0, False)
        assert score == 0.0
    else:
        score, factors = scorer.score(root_cause, raw_tx["customer_segment"], 0, False)

    # Step 3: Strategy Proposal (even if LLM suggests retry)
    proposal_dict = strategy_gen.generate_strategy({
        "root_cause": root_cause,
        "recoverability_score": score,
        "customer_segment": raw_tx["customer_segment"],
        "previous_retry_count": 0,
        "is_subscription": False,
    })
    proposal = PlaybookProposal(**proposal_dict)

    # Step 4: Policy Gate MUST intercept and override
    tx_ctx = TransactionContext(
        transaction_id=raw_tx["transaction_id"],
        customer_id=raw_tx["customer_id"],
        customer_segment=raw_tx["customer_segment"],
        amount=raw_tx["amount"],
        decline_code=raw_tx["decline_code"],
        decline_message=raw_tx["decline_message"],
        previous_retry_count=raw_tx["previous_retry_count"],
        fraud_flag=raw_tx["fraud_flag"],
        is_subscription=raw_tx["is_subscription"],
    )
    approved, verdict, overrides = policy_gate.evaluate(tx_ctx, proposal)

    assert verdict == "OVERRIDDEN"
    assert approved.action == "escalate_human"
    assert approved.max_retries == 0
    assert any("FRAUD" in o["rule"] for o in overrides)

    # Step 5: Simulator confirms 3 false retries avoided
    import random
    rng = random.Random(42)
    sim_res = simulator.simulate_single(raw_tx, approved.to_dict(), score, rng)
    assert sim_res["simulated_outcome_ai"] == "SKIPPED"
    assert sim_res["simulated_outcome_baseline"] == "FAILED"
    assert sim_res["false_retries_avoided_count"] == 3


def test_edge_case_2_expired_card_backup_mandate():
    """
    EDGE CASE 2:
    High-value customer with an expired card, but secondary UPI Autopay mandate is saved.
    The system must:
    1. Classify root cause as CARD_EXPIRED
    2. Recognize customer is high-value subscription
    3. Generate playbook to notify customer via WhatsApp with 0 blind retries
    4. Policy Gate passes the playbook cleanly
    5. Simulator confirms recovery without burning blind retries, avoiding 3 useless retries.
    """
    classifier = Classifier()
    scorer = Scorer()
    strategy_gen = StrategyGenerator()
    policy_gate = PolicyGate()
    simulator = Simulator(seed=42)

    raw_tx = {
        "transaction_id": "tx_edge_exp_backup_002",
        "customer_id": "cust_edge_9902",
        "customer_segment": "high_value",
        "amount": 48000.0,
        "decline_code": "CARD_EXPIRED",
        "decline_message": "Primary card lapsed. Secondary mandate on UPI Autopay is linked in customer wallet.",
        "previous_retry_count": 0,
        "fraud_flag": False,
        "is_subscription": True,
        "edge_case_tag": "expired_card_backup_mandate",
    }

    # Step 1: Classifier
    root_cause, rationale = classifier.classify(raw_tx["decline_code"], raw_tx["decline_message"])
    assert root_cause == "CARD_EXPIRED"

    # Step 2: Scorer
    score, factors = scorer.score(root_cause, raw_tx["customer_segment"], 0, True)
    assert score > 0.40  # Boosted by high-value + subscription

    # Step 3: Strategy Generator
    proposal_dict = strategy_gen.generate_strategy({
        "root_cause": root_cause,
        "recoverability_score": score,
        "customer_segment": raw_tx["customer_segment"],
        "previous_retry_count": 0,
        "is_subscription": True,
        "edge_case_tag": raw_tx["edge_case_tag"],
    })
    proposal = PlaybookProposal(**proposal_dict)
    assert proposal.action == "notify_customer"
    assert proposal.channel in ["whatsapp", "in_app"]
    assert proposal.max_retries == 0

    # Step 4: Policy Gate
    tx_ctx = TransactionContext(
        transaction_id=raw_tx["transaction_id"],
        customer_id=raw_tx["customer_id"],
        customer_segment=raw_tx["customer_segment"],
        amount=raw_tx["amount"],
        decline_code=raw_tx["decline_code"],
        decline_message=raw_tx["decline_message"],
        previous_retry_count=raw_tx["previous_retry_count"],
        fraud_flag=raw_tx["fraud_flag"],
        is_subscription=raw_tx["is_subscription"],
    )
    approved, verdict, overrides = policy_gate.evaluate(tx_ctx, proposal)
    assert verdict == "PASSED"
    assert approved.action == "notify_customer"

    # Step 5: Simulator
    import random
    rng = random.Random(42)
    sim_res = simulator.simulate_single(raw_tx, approved.to_dict(), score, rng)
    assert sim_res["simulated_outcome_ai"] == "RECOVERED"
    assert sim_res["simulated_outcome_baseline"] == "FAILED"
    assert sim_res["false_retries_avoided_count"] == 3
