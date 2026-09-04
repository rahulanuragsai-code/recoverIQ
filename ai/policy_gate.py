"""
RecoverIQ - Pipeline Step 4: Deterministic Policy Gate
Hard-coded, deterministic safety rules that strictly validate and override LLM proposals.
Safety-critical layer: LLM outputs are NEVER executed without passing this gate.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class TransactionContext:
    transaction_id: str
    customer_id: str
    customer_segment: str
    amount: float
    decline_code: str
    decline_message: str
    previous_retry_count: int
    fraud_flag: bool
    is_subscription: bool
    customer_retries_today: int = 0
    edge_case_tag: Optional[str] = None


@dataclass
class PlaybookProposal:
    action: str  # retry_now | retry_scheduled | notify_customer | escalate_human | do_not_retry
    channel: str  # email | sms | whatsapp | in_app | none
    retry_delay_hours: int
    max_retries: int
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "channel": self.channel,
            "retry_delay_hours": self.retry_delay_hours,
            "max_retries": self.max_retries,
            "rationale": self.rationale,
        }


class PolicyGate:
    """
    Deterministic Safety Gate.
    The gate ALWAYS wins against any LLM proposal.
    """

    MAX_CUMULATIVE_RETRIES = 3
    MIN_COOLDOWN_HOURS = 12
    MAX_CUSTOMER_RETRIES_PER_DAY = 2

    def evaluate(
        self,
        tx: TransactionContext,
        proposal: PlaybookProposal,
    ) -> Tuple[PlaybookProposal, str, List[Dict[str, Any]]]:
        """
        Validates the proposed playbook against safety rules.
        Returns:
            approved_playbook (PlaybookProposal)
            verdict (str: 'PASSED' | 'OVERRIDDEN')
            overrides (List[Dict[str, Any]])
        """
        overrides: List[Dict[str, Any]] = []

        action = proposal.action
        channel = proposal.channel
        retry_delay_hours = proposal.retry_delay_hours
        max_retries = proposal.max_retries
        rationale = proposal.rationale

        # ----------------------------------------------------------------------
        # RULE 1: FRAUD ZERO TOLERANCE
        # Never retry if fraud_flag is True or decline_code is SUSPECTED_FRAUD.
        # ----------------------------------------------------------------------
        is_fraud = tx.fraud_flag or tx.decline_code.upper() == "SUSPECTED_FRAUD"
        if is_fraud:
            if action in ["retry_now", "retry_scheduled"] or max_retries > 0 or action != "escalate_human":
                orig = {
                    "action": action,
                    "max_retries": max_retries,
                    "channel": channel,
                }
                action = "escalate_human"
                max_retries = 0
                channel = "none"
                retry_delay_hours = 0
                rationale = (
                    "POLICY OVERRIDE: Fraud flag active. Zero automated retries permitted; "
                    "escalated immediately to fraud risk operations."
                )
                overrides.append({
                    "rule": "RULE_FRAUD_ZERO_TOLERANCE",
                    "reason": "Transaction flagged for suspected fraud. Automated retries strictly prohibited.",
                    "original_value": orig,
                    "overridden_value": {"action": action, "max_retries": 0, "channel": "none"},
                })

        # ----------------------------------------------------------------------
        # RULE 2: MAX RETRIES CAP (3 TOTAL RETRIES LIFETIME)
        # ----------------------------------------------------------------------
        if not is_fraud:
            if tx.previous_retry_count >= self.MAX_CUMULATIVE_RETRIES:
                if action in ["retry_now", "retry_scheduled"]:
                    orig_action = action
                    action = "notify_customer" if tx.is_subscription else "do_not_retry"
                    max_retries = 0
                    retry_delay_hours = 0
                    channel = "whatsapp" if tx.customer_segment == "high_value" else "email"
                    rationale = (
                        f"POLICY OVERRIDE: Transaction reached max cumulative retry limit ({tx.previous_retry_count}/3). "
                        f"Automated retries stopped; customer notification dispatched."
                    )
                    overrides.append({
                        "rule": "RULE_MAX_RETRIES_CAP_EXCEEDED",
                        "reason": f"Cumulative retries already at limit ({tx.previous_retry_count}/3). Further retries prohibited.",
                        "original_value": {"action": orig_action, "max_retries": proposal.max_retries},
                        "overridden_value": {"action": action, "max_retries": 0, "channel": channel},
                    })
            elif tx.previous_retry_count + max_retries > self.MAX_CUMULATIVE_RETRIES:
                remaining_allowed = max(0, self.MAX_CUMULATIVE_RETRIES - tx.previous_retry_count)
                overrides.append({
                    "rule": "RULE_MAX_RETRIES_CLAMPED",
                    "reason": (
                        f"Proposed {max_retries} retries exceeds remaining quota ({remaining_allowed}) "
                        f"under lifetime cap of {self.MAX_CUMULATIVE_RETRIES}."
                    ),
                    "original_value": {"max_retries": max_retries},
                    "overridden_value": {"max_retries": remaining_allowed},
                })
                max_retries = remaining_allowed

        # ----------------------------------------------------------------------
        # RULE 3: MINIMUM 12H COOLDOWN BETWEEN RETRIES
        # ----------------------------------------------------------------------
        if not is_fraud and action == "retry_scheduled" and retry_delay_hours < self.MIN_COOLDOWN_HOURS:
            overrides.append({
                "rule": "RULE_MIN_COOLDOWN_12H",
                "reason": f"Scheduled retry delay of {retry_delay_hours}h violates 12h minimum banking cooldown requirement.",
                "original_value": {"retry_delay_hours": retry_delay_hours},
                "overridden_value": {"retry_delay_hours": self.MIN_COOLDOWN_HOURS},
            })
            retry_delay_hours = self.MIN_COOLDOWN_HOURS

        # Disallow immediate retry for repeat failures (previous_retry_count > 0)
        if not is_fraud and tx.previous_retry_count > 0 and action == "retry_now":
            overrides.append({
                "rule": "RULE_MIN_COOLDOWN_12H_REPEAT_FAILURE",
                "reason": "Immediate retry disallowed on repeat failure (cooldown required to prevent gateway penalties).",
                "original_value": {"action": "retry_now", "retry_delay_hours": 0},
                "overridden_value": {"action": "retry_scheduled", "retry_delay_hours": self.MIN_COOLDOWN_HOURS},
            })
            action = "retry_scheduled"
            retry_delay_hours = self.MIN_COOLDOWN_HOURS

        # ----------------------------------------------------------------------
        # RULE 4: CUSTOMER DAILY VELOCITY LIMIT (MAX 2 RETRIES PER DAY)
        # ----------------------------------------------------------------------
        if not is_fraud and action in ["retry_now", "retry_scheduled"] and tx.customer_retries_today >= self.MAX_CUSTOMER_RETRIES_PER_DAY:
            orig_action = action
            action = "notify_customer"
            max_retries = 0
            retry_delay_hours = 0
            channel = "whatsapp" if tx.customer_segment == "high_value" else "email"
            rationale = (
                f"POLICY OVERRIDE: Customer {tx.customer_id} reached daily retry limit ({tx.customer_retries_today}/2). "
                f"Blocked further retries in 24h window to avoid card blocking."
            )
            overrides.append({
                "rule": "RULE_CUSTOMER_DAILY_LIMIT",
                "reason": f"Customer exceeded maximum 2 retry attempts in 24 hours ({tx.customer_retries_today}/2).",
                "original_value": {"action": orig_action, "max_retries": proposal.max_retries},
                "overridden_value": {"action": action, "max_retries": 0},
            })

        # ----------------------------------------------------------------------
        # RULE 5: SANITY ENFORCEMENT ON NON-RETRY ACTIONS
        # ----------------------------------------------------------------------
        if action in ["do_not_retry", "escalate_human", "notify_customer"] and max_retries > 0:
            overrides.append({
                "rule": "RULE_NON_RETRY_ACTION_MAX_RETRIES_ZERO",
                "reason": f"Action '{action}' is a non-retry action; max_retries must be 0.",
                "original_value": {"max_retries": max_retries},
                "overridden_value": {"max_retries": 0},
            })
            max_retries = 0

        verdict = "OVERRIDDEN" if len(overrides) > 0 else "PASSED"

        approved = PlaybookProposal(
            action=action,
            channel=channel,
            retry_delay_hours=retry_delay_hours,
            max_retries=max_retries,
            rationale=rationale,
        )

        return approved, verdict, overrides
