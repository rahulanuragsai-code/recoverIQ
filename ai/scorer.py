"""
RecoverIQ - Pipeline Step 2: Recoverability Scorer
A fully deterministic, inspectable mathematical scoring engine (NOT an LLM black box).
Calculates recoverability probability [0.0 - 1.0] and decomposes key driving factors.
"""

from typing import Any, Dict, List, Tuple

# Base baseline recoverability by root cause category
BASE_WEIGHTS = {
    "NETWORK_TIMEOUT": 0.88,      # Transient infrastructure glitch; highly recoverable
    "PROCESSING_ERROR": 0.82,     # Switch processor glitch; high immediate recovery rate
    "INSUFFICIENT_FUNDS": 0.65,   # Recoverable upon salary cycle, payday, or balance top-up
    "ISSUER_DECLINE": 0.45,       # Standing instruction/mandate block; moderate recovery
    "CARD_EXPIRED": 0.35,         # Requires manual customer credential update
    "INVALID_CVV": 0.28,          # User input error; requires active customer re-entry
    "SUSPECTED_FRAUD": 0.00,      # High risk; automated recovery strictly prohibited
}

# Segment modifiers based on customer solvency & retention affinity
SEGMENT_MODIFIERS = {
    "high_value": 0.15,   # High intent, premium account, strong payment history
    "regular": 0.05,      # Established platform relationship
    "new": 0.00,          # First-time or low-history transaction
}

# Retry fatigue penalty (exponential drop with each failed attempt)
RETRY_PENALTIES = {
    0: 0.00,
    1: -0.12,
    2: -0.26,
    3: -0.45,
}

SUBSCRIPTION_BONUS = 0.10  # Higher lifetime value and recurring commitment


class Scorer:
    def score(
        self,
        root_cause: str,
        customer_segment: str,
        previous_retry_count: int,
        is_subscription: bool,
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Calculates deterministic recoverability score [0.0, 1.0] and driving factors.
        Returns (score, top_factors).
        """
        # Hard zero for fraud
        if root_cause == "SUSPECTED_FRAUD":
            return 0.0, [
                {
                    "factor": "SUSPECTED_FRAUD_FLAG",
                    "impact": -1.0,
                    "description": "Critical security risk: Transaction flagged by fraud engine. Recoverability set to 0.",
                }
            ]

        base = BASE_WEIGHTS.get(root_cause, 0.45)
        seg_mod = SEGMENT_MODIFIERS.get(customer_segment, 0.0)
        retries_clamped = min(max(previous_retry_count, 0), 3)
        retry_mod = RETRY_PENALTIES.get(retries_clamped, -0.45)
        sub_mod = SUBSCRIPTION_BONUS if is_subscription else 0.0

        raw_score = base + seg_mod + retry_mod + sub_mod
        final_score = round(max(0.01, min(0.99, raw_score)), 3)

        # Factor decomposition
        factors: List[Dict[str, Any]] = []

        # 1. Root Cause Factor
        factors.append({
            "factor": f"ROOT_CAUSE_{root_cause}",
            "impact": round(base - 0.50, 3),
            "description": f"Base failure root cause '{root_cause}' provides baseline recoverability of {int(base * 100)}%.",
        })

        # 2. Retry Fatigue Factor
        if previous_retry_count > 0:
            factors.append({
                "factor": "RETRY_FATIGUE",
                "impact": retry_mod,
                "description": f"{previous_retry_count} previous failed attempts reduce recovery odds by {int(abs(retry_mod) * 100)}%.",
            })

        # 3. Customer Segment Factor
        if seg_mod > 0:
            factors.append({
                "factor": f"CUSTOMER_SEGMENT_{customer_segment.upper()}",
                "impact": seg_mod,
                "description": f"{customer_segment.replace('_', ' ').title()} customer segment confers +{int(seg_mod * 100)}% recovery confidence.",
            })

        # 4. Subscription Bonus
        if is_subscription:
            factors.append({
                "factor": "SUBSCRIPTION_RECURRING",
                "impact": sub_mod,
                "description": "Recurring subscription status indicates high customer retention intent (+10%).",
            })

        # Sort factors by absolute magnitude of impact
        factors.sort(key=lambda x: abs(x["impact"]), reverse=True)
        top_factors = factors[:3]

        return final_score, top_factors
