"""
Tests for Recovery Simulator reproducibility with fixed seed 42.
"""

from ai.simulator import Simulator


def test_simulator_reproducibility():
    sim1 = Simulator(seed=42)
    sim2 = Simulator(seed=42)

    sample_txs = [
        {
            "transaction": {
                "transaction_id": f"tx_{i}",
                "amount": 1000.0 * i,
                "decline_code": "INSUFFICIENT_FUNDS",
                "fraud_flag": False,
                "previous_retry_count": 0,
            },
            "approved_playbook": {
                "action": "retry_scheduled",
                "channel": "whatsapp",
                "retry_delay_hours": 24,
                "max_retries": 1,
            },
            "recoverability_score": 0.70,
            "policy_gate_verdict": "PASSED",
        }
        for i in range(1, 20)
    ]

    _, summary1 = sim1.simulate_batch(sample_txs)
    _, summary2 = sim2.simulate_batch(sample_txs)

    assert summary1["amount_recovered_ai"] == summary2["amount_recovered_ai"]
    assert summary1["recovery_rate_ai"] == summary2["recovery_rate_ai"]
    assert summary1["false_retries_avoided"] == summary2["false_retries_avoided"]
