"""
Tests for RecoverIQ Deterministic Policy Gate.
Safety-critical tests ensuring that hard-coded business rules ALWAYS override LLM proposals.
"""

import pytest
from ai.policy_gate import PolicyGate, PlaybookProposal, TransactionContext


@pytest.fixture
def policy_gate():
    return PolicyGate()


def test_fraud_flag_strictly_blocks_retry(policy_gate):
    """
    SAFETY TEST: An LLM proposing an aggressive retry on a fraudulent transaction
    MUST be strictly overridden by the Policy Gate.
    """
    tx = TransactionContext(
        transaction_id="tx_test_fraud_01",
        customer_id="cust_test_100",
        customer_segment="high_value",
        amount=50000.0,
        decline_code="ISSUER_DECLINE",
        decline_message="Decline: 05 - Do Not Honor",
        previous_retry_count=0,
        fraud_flag=True,  # Suspected Fraud
        is_subscription=True,
    )

    hallucinated_llm_proposal = PlaybookProposal(
        action="retry_now",
        channel="email",
        retry_delay_hours=0,
        max_retries=2,
        rationale="Customer is high value subscription, retry immediately to recover funds.",
    )

    approved, verdict, overrides = policy_gate.evaluate(tx, hallucinated_llm_proposal)

    assert verdict == "OVERRIDDEN"
    assert approved.action in ["escalate_human", "do_not_retry"]
    assert approved.max_retries == 0
    assert any("FRAUD_ZERO_TOLERANCE" in o["rule"] for o in overrides)


def test_fraud_camouflage_edge_case(policy_gate):
    """
    EDGE CASE 1: Decline message misleadingly looks like insufficient funds,
    but fraud_flag is True. Policy Gate must strictly catch and override.
    """
    tx = TransactionContext(
        transaction_id="tx_edge_fraud_001",
        customer_id="cust_edge_9901",
        customer_segment="regular",
        amount=18500.0,
        decline_code="ISSUER_DECLINE",
        decline_message="Transaction cannot be processed: balance check failed (code 51)",
        previous_retry_count=0,
        fraud_flag=True,
        is_subscription=False,
    )

    llm_proposal = PlaybookProposal(
        action="retry_scheduled",
        channel="sms",
        retry_delay_hours=24,
        max_retries=1,
        rationale="Balance check failed, scheduled retry after payday.",
    )

    approved, verdict, overrides = policy_gate.evaluate(tx, llm_proposal)

    assert verdict == "OVERRIDDEN"
    assert approved.action == "escalate_human"
    assert approved.max_retries == 0
    assert any("FRAUD_ZERO_TOLERANCE" in o["rule"] for o in overrides)


def test_max_retries_capped_at_three_total(policy_gate):
    """
    SAFETY TEST: Hard cap of 3 total retries per transaction.
    If previous_retry_count is 3, no further retries may be scheduled.
    """
    tx = TransactionContext(
        transaction_id="tx_test_retry_cap_01",
        customer_id="cust_test_101",
        customer_segment="regular",
        amount=4500.0,
        decline_code="INSUFFICIENT_FUNDS",
        decline_message="Insufficient balance",
        previous_retry_count=3,  # Already tried 3 times
        fraud_flag=False,
        is_subscription=True,
    )

    llm_proposal = PlaybookProposal(
        action="retry_scheduled",
        channel="whatsapp",
        retry_delay_hours=48,
        max_retries=1,
        rationale="Retry after salary cycle.",
    )

    approved, verdict, overrides = policy_gate.evaluate(tx, llm_proposal)

    assert verdict == "OVERRIDDEN"
    assert approved.action in ["notify_customer", "do_not_retry"]
    assert approved.max_retries == 0
    assert any("MAX_RETRIES_CAP" in o["rule"] for o in overrides)


def test_retry_budget_clamping(policy_gate):
    """
    SAFETY TEST: If previous_retries = 2, and LLM proposes max_retries = 2,
    total would be 4. Gate must clamp remaining retries to 1.
    """
    tx = TransactionContext(
        transaction_id="tx_test_clamp_02",
        customer_id="cust_test_102",
        customer_segment="regular",
        amount=1200.0,
        decline_code="INSUFFICIENT_FUNDS",
        decline_message="Insufficient funds",
        previous_retry_count=2,
        fraud_flag=False,
        is_subscription=True,
    )

    llm_proposal = PlaybookProposal(
        action="retry_scheduled",
        channel="email",
        retry_delay_hours=24,
        max_retries=2,
        rationale="Retry twice over next 48 hours.",
    )

    approved, verdict, overrides = policy_gate.evaluate(tx, llm_proposal)

    assert verdict == "OVERRIDDEN"
    assert approved.max_retries == 1
    assert any("MAX_RETRIES_CLAMPED" in o["rule"] for o in overrides)


def test_minimum_12h_cooldown_enforcement(policy_gate):
    """
    SAFETY TEST: Any scheduled retry must respect a minimum 12-hour cooldown.
    """
    tx = TransactionContext(
        transaction_id="tx_test_cooldown_01",
        customer_id="cust_test_103",
        customer_segment="new",
        amount=899.0,
        decline_code="INSUFFICIENT_FUNDS",
        decline_message="Account balance low",
        previous_retry_count=0,
        fraud_flag=False,
        is_subscription=False,
    )

    llm_proposal = PlaybookProposal(
        action="retry_scheduled",
        channel="in_app",
        retry_delay_hours=3,  # Violates 12h rule!
        max_retries=1,
        rationale="Quick retry in 3 hours.",
    )

    approved, verdict, overrides = policy_gate.evaluate(tx, llm_proposal)

    assert verdict == "OVERRIDDEN"
    assert approved.retry_delay_hours >= 12
    assert any("MIN_COOLDOWN_12H" in o["rule"] for o in overrides)


def test_repeat_failure_immediate_retry_blocked(policy_gate):
    """
    SAFETY TEST: An already-failed transaction (previous_retry_count > 0)
    cannot be immediately retried without a cooldown period.
    """
    tx = TransactionContext(
        transaction_id="tx_test_repeat_01",
        customer_id="cust_test_104",
        customer_segment="regular",
        amount=3400.0,
        decline_code="NETWORK_TIMEOUT",
        decline_message="Timeout awaiting issuer",
        previous_retry_count=1,
        fraud_flag=False,
        is_subscription=True,
    )

    llm_proposal = PlaybookProposal(
        action="retry_now",
        channel="none",
        retry_delay_hours=0,
        max_retries=1,
        rationale="Retry immediately since network might have recovered.",
    )

    approved, verdict, overrides = policy_gate.evaluate(tx, llm_proposal)

    assert verdict == "OVERRIDDEN"
    assert approved.action == "retry_scheduled"
    assert approved.retry_delay_hours >= 12
    assert any("MIN_COOLDOWN_12H" in o["rule"] for o in overrides)


def test_customer_daily_velocity_limit(policy_gate):
    """
    SAFETY TEST: Never more than 2 retry actions per customer per day.
    """
    tx = TransactionContext(
        transaction_id="tx_test_velocity_01",
        customer_id="cust_test_velocity_105",
        customer_segment="regular",
        amount=2500.0,
        decline_code="INSUFFICIENT_FUNDS",
        decline_message="Low balance",
        previous_retry_count=0,
        fraud_flag=False,
        is_subscription=False,
        customer_retries_today=2,  # Already hit daily cap
    )

    llm_proposal = PlaybookProposal(
        action="retry_scheduled",
        channel="sms",
        retry_delay_hours=24,
        max_retries=1,
        rationale="Retry tomorrow.",
    )

    approved, verdict, overrides = policy_gate.evaluate(tx, llm_proposal)

    assert verdict == "OVERRIDDEN"
    assert approved.action in ["notify_customer", "escalate_human", "do_not_retry"]
    assert approved.max_retries == 0
    assert any("CUSTOMER_DAILY_LIMIT" in o["rule"] for o in overrides)


def test_clean_playbook_passes_unmodified(policy_gate):
    """
    A well-behaved playbook respecting all rules passes cleanly with PASSED status.
    """
    tx = TransactionContext(
        transaction_id="tx_test_clean_01",
        customer_id="cust_test_106",
        customer_segment="high_value",
        amount=15000.0,
        decline_code="INSUFFICIENT_FUNDS",
        decline_message="Insufficient balance",
        previous_retry_count=0,
        fraud_flag=False,
        is_subscription=True,
        customer_retries_today=0,
    )

    valid_proposal = PlaybookProposal(
        action="retry_scheduled",
        channel="whatsapp",
        retry_delay_hours=24,
        max_retries=1,
        rationale="Notify customer on WhatsApp and retry after 24 hours.",
    )

    approved, verdict, overrides = policy_gate.evaluate(tx, valid_proposal)

    assert verdict == "PASSED"
    assert len(overrides) == 0
    assert approved.action == "retry_scheduled"
    assert approved.retry_delay_hours == 24
    assert approved.max_retries == 1
