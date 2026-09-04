"""
Tests for Root Cause Classifier.
"""

from ai.classifier import Classifier


def test_clear_decline_code():
    classifier = Classifier()
    root, rationale = classifier.classify("CARD_EXPIRED", "Card validity period expired")
    assert root == "CARD_EXPIRED"
    assert "deterministically" in rationale.lower()


def test_ambiguous_message_resolution():
    classifier = Classifier()
    # Code says ISSUER_DECLINE, but message mentions daily ceiling / balance check
    root, rationale = classifier.classify("ISSUER_DECLINE", "05: Customer reported daily debit ceiling reached for current cycle")
    assert root == "INSUFFICIENT_FUNDS"


def test_network_timeout_resolution():
    classifier = Classifier()
    root, rationale = classifier.classify("PROCESSING_ERROR", "Switch ping failed after 45000ms: host unresponsive")
    assert root == "NETWORK_TIMEOUT"
