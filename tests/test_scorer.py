"""
Tests for Recoverability Scorer determinism and factor attribution.
"""

from ai.scorer import Scorer


def test_scorer_determinism():
    scorer = Scorer()
    # Identical inputs must yield identical scores and factor sets
    s1, f1 = scorer.score("INSUFFICIENT_FUNDS", "high_value", 0, True)
    s2, f2 = scorer.score("INSUFFICIENT_FUNDS", "high_value", 0, True)

    assert s1 == s2
    assert len(f1) == len(f2)
    assert f1[0]["factor"] == f2[0]["factor"]


def test_scorer_fraud_zero():
    scorer = Scorer()
    score, factors = scorer.score("SUSPECTED_FRAUD", "high_value", 0, True)
    assert score == 0.0
    assert factors[0]["factor"] == "SUSPECTED_FRAUD_FLAG"


def test_scorer_retry_decay():
    scorer = Scorer()
    s0, _ = scorer.score("INSUFFICIENT_FUNDS", "regular", 0, False)
    s1, _ = scorer.score("INSUFFICIENT_FUNDS", "regular", 1, False)
    s2, _ = scorer.score("INSUFFICIENT_FUNDS", "regular", 2, False)
    s3, _ = scorer.score("INSUFFICIENT_FUNDS", "regular", 3, False)

    # Monotonically decreasing
    assert s0 > s1 > s2 > s3
