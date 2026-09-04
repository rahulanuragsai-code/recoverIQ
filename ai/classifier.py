"""
RecoverIQ - Pipeline Step 1: Root Cause Classifier
Maps decline_code and decline_message to a canonical root_cause category.
Deterministic for unambiguous decline codes; delegates to LLM for messy/ambiguous messages.
"""

from typing import Dict, Tuple
from ai.llm_client import BaseLLMClient, get_llm_client

VALID_ROOT_CAUSES = {
    "INSUFFICIENT_FUNDS",
    "CARD_EXPIRED",
    "ISSUER_DECLINE",
    "INVALID_CVV",
    "NETWORK_TIMEOUT",
    "SUSPECTED_FRAUD",
    "PROCESSING_ERROR",
}

# Clear decline codes with standard messages that do not require LLM parsing
UNAMBIGUOUS_CODES = {
    "CARD_EXPIRED": "Card validity period expired",
    "INVALID_CVV": "Security code verification failed (CVV/CVC)",
    "SUSPECTED_FRAUD": "Transaction blocked by risk engine: velocity check failed",
}


class Classifier:
    def __init__(self, llm_client: BaseLLMClient = None):
        self.llm_client = llm_client or get_llm_client()

    def classify(self, decline_code: str, decline_message: str) -> Tuple[str, str]:
        """
        Classifies transaction failure into canonical root cause.
        Returns (root_cause, rationale).
        """
        # 1. Deterministic fast-path for obvious decline codes without messy/ambiguous text
        clean_code = decline_code.strip().upper()
        clean_msg = decline_message.strip()

        # Check if the message is ambiguous or contains conflicting signals
        is_ambiguous = (
            "code 51" in clean_msg  # Balance error disguised under generic decline
            or "secondary mandate" in clean_msg.lower()
            or "standing instruction" in clean_msg.lower()
            or "switch ping" in clean_msg.lower()
            or "ceiling reached" in clean_msg.lower()
            or clean_code == "ISSUER_DECLINE"  # Always ambiguous generic decline code
        )

        if not is_ambiguous and clean_code in VALID_ROOT_CAUSES:
            return clean_code, f"Deterministically classified via standard gateway decline code '{clean_code}'."

        # 2. Ambiguous or messy message: Delegate to LLM classifier
        llm_result = self.llm_client.classify_root_cause(clean_code, clean_msg)
        root_cause = llm_result.get("root_cause", clean_code)
        rationale = llm_result.get("rationale", "Classified via LLM semantic text analysis.")

        # Ensure valid enum
        if root_cause not in VALID_ROOT_CAUSES:
            root_cause = "ISSUER_DECLINE"

        return root_cause, rationale
