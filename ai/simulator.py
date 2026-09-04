"""
RecoverIQ - Pipeline Step 5: Recovery Simulator & Baseline Comparator
Simulates the approved recovery playbook head-to-head against a naive 3x retry baseline.
Uses a deterministic random seed (42) to guarantee 100% reproducible results for evaluators.
"""

import random
from typing import Any, Dict, List, Tuple


class Simulator:
    def __init__(self, seed: int = 42):
        self.seed = seed

    def simulate_single(
        self,
        tx_data: Dict[str, Any],
        approved_playbook: Dict[str, Any],
        recoverability_score: float,
        rng: random.Random,
    ) -> Dict[str, Any]:
        """
        Simulate outcome for a single transaction under both AI policy and Naive Baseline.
        """
        amount = float(tx_data.get("amount", 0.0))
        fraud_flag = bool(tx_data.get("fraud_flag", False))
        decline_code = tx_data.get("decline_code", "")
        root_cause = tx_data.get("root_cause", decline_code)
        prev_retries = int(tx_data.get("previous_retry_count", 0))
        edge_tag = tx_data.get("edge_case_tag")

        action = approved_playbook.get("action", "retry_scheduled")
        channel = approved_playbook.get("channel", "email")
        delay_hours = approved_playbook.get("retry_delay_hours", 0)
        max_retries = approved_playbook.get("max_retries", 0)

        # ----------------------------------------------------------------------
        # 1. AI PLAYBOOK SIMULATION
        # ----------------------------------------------------------------------
        ai_outcome = "FAILED"
        ai_retries_used = 0

        if action in ["do_not_retry", "escalate_human"]:
            ai_outcome = "SKIPPED"
            ai_retries_used = 0
        elif action == "notify_customer":
            # Direct notification (WhatsApp, In-App, Email) for credential updates or backup mandate
            ai_retries_used = 0
            if edge_tag == "expired_card_backup_mandate":
                # Edge Case 2: Customer has linked UPI Autopay backup mandate
                # High-value customer with 1-click fallback notification converts at 92%
                p_success = 0.92
            elif root_cause in ["CARD_EXPIRED", "INVALID_CVV"]:
                # Customer prompted to re-enter details
                p_success = min(0.78, recoverability_score + 0.25)
            else:
                p_success = recoverability_score

            if rng.random() < p_success:
                ai_outcome = "RECOVERED"
            else:
                ai_outcome = "FAILED"
        elif action in ["retry_now", "retry_scheduled"]:
            # Probability adjustments for timing and channel
            p_attempt = recoverability_score
            if delay_hours >= 12:
                p_attempt += 0.08  # Funds replenishment advantage
            if channel in ["whatsapp", "sms"]:
                p_attempt += 0.04  # Timely customer awareness

            p_attempt = max(0.05, min(0.95, p_attempt))

            for attempt in range(1, max_retries + 1):
                ai_retries_used = attempt
                if rng.random() < p_attempt:
                    ai_outcome = "RECOVERED"
                    break

        # ----------------------------------------------------------------------
        # 2. NAIVE BASELINE SIMULATION
        # Blindly retries immediately 3 times regardless of root cause or fraud
        # ----------------------------------------------------------------------
        baseline_outcome = "FAILED"
        baseline_retries_used = 3  # Naive baseline exhausts all 3 attempts

        if fraud_flag or root_cause == "SUSPECTED_FRAUD":
            # Fraud transactions always fail on blind retries
            baseline_outcome = "FAILED"
            baseline_retries_used = 3
        elif root_cause in ["CARD_EXPIRED", "INVALID_CVV"]:
            # Expired plastic / wrong CVV will NEVER succeed without customer intervention
            baseline_outcome = "FAILED"
            baseline_retries_used = 3
        elif prev_retries >= 3:
            # Already exhausted; gateway refuses
            baseline_outcome = "FAILED"
            baseline_retries_used = 3
        else:
            # Blind immediate retry: penalty of -0.22 for no cooldown / no intelligence
            p_baseline = max(0.02, min(0.70, recoverability_score - 0.22))
            baseline_retries_used = 0
            for attempt in range(1, 4):
                baseline_retries_used = attempt
                if rng.random() < p_baseline:
                    baseline_outcome = "RECOVERED"
                    break

        # ----------------------------------------------------------------------
        # 3. FALSE RETRIES AVOIDED CALCULATION
        # ----------------------------------------------------------------------
        false_retries_avoided = 0
        # Wasted retries that baseline fired on impossible transactions
        if fraud_flag or root_cause == "SUSPECTED_FRAUD":
            false_retries_avoided = 3  # Prevented 3 risky retries on fraud
        elif root_cause in ["CARD_EXPIRED", "INVALID_CVV"] and action == "notify_customer":
            false_retries_avoided = 3  # Replaced 3 blind failures with notification
        elif prev_retries >= 3:
            false_retries_avoided = 3  # Prevented 3 futile retries on maxed-out card
        elif baseline_retries_used > ai_retries_used:
            false_retries_avoided = baseline_retries_used - ai_retries_used

        return {
            "simulated_outcome_ai": ai_outcome,
            "simulated_retries_ai": ai_retries_used,
            "simulated_outcome_baseline": baseline_outcome,
            "simulated_retries_baseline": baseline_retries_used,
            "false_retry_avoided": false_retries_avoided > 0,
            "false_retries_avoided_count": false_retries_avoided,
        }

    def simulate_batch(
        self,
        transactions_with_playbooks: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Run deterministic batch simulation over an entire dataset.
        Returns:
            updated_transactions: list with simulation fields added
            metrics_summary: comprehensive KPI comparison
        """
        rng = random.Random(self.seed)

        total_tx = len(transactions_with_playbooks)
        amount_at_risk = 0.0
        amount_rec_ai = 0.0
        amount_rec_baseline = 0.0
        count_rec_ai = 0
        count_rec_baseline = 0
        total_false_retries_avoided = 0
        policy_overrides_count = 0

        root_cause_counts: Dict[str, int] = {}
        action_counts: Dict[str, int] = {}

        results: List[Dict[str, Any]] = []

        for item in transactions_with_playbooks:
            tx = item["transaction"]
            approved_playbook = item["approved_playbook"]
            rec_score = item["recoverability_score"]
            verdict = item.get("policy_gate_verdict", "PASSED")

            if verdict == "OVERRIDDEN":
                policy_overrides_count += 1

            action = approved_playbook.get("action", "unknown")
            action_counts[action] = action_counts.get(action, 0) + 1

            root_cause = tx.get("root_cause", "UNKNOWN")
            root_cause_counts[root_cause] = root_cause_counts.get(root_cause, 0) + 1

            sim_res = self.simulate_single(tx, approved_playbook, rec_score, rng)

            amt = float(tx.get("amount", 0.0))
            amount_at_risk += amt

            if sim_res["simulated_outcome_ai"] == "RECOVERED":
                amount_rec_ai += amt
                count_rec_ai += 1

            if sim_res["simulated_outcome_baseline"] == "RECOVERED":
                amount_rec_baseline += amt
                count_rec_baseline += 1

            total_false_retries_avoided += sim_res["false_retries_avoided_count"]

            # Merge simulation result into record
            merged_tx = dict(tx)
            merged_tx.update(sim_res)
            results.append(merged_tx)

        rec_rate_ai = round((amount_rec_ai / amount_at_risk * 100) if amount_at_risk > 0 else 0.0, 2)
        rec_rate_baseline = round((amount_rec_baseline / amount_at_risk * 100) if amount_at_risk > 0 else 0.0, 2)
        uplift_pct = round(rec_rate_ai - rec_rate_baseline, 2)

        summary = {
            "seed": self.seed,
            "total_transactions": total_tx,
            "amount_at_risk": round(amount_at_risk, 2),
            "amount_recovered_ai": round(amount_rec_ai, 2),
            "amount_recovered_baseline": round(amount_rec_baseline, 2),
            "recovery_rate_ai": rec_rate_ai,
            "recovery_rate_baseline": rec_rate_baseline,
            "recovery_rate_uplift_pct": uplift_pct,
            "false_retries_avoided": total_false_retries_avoided,
            "policy_overrides_count": policy_overrides_count,
            "count_recovered_ai": count_rec_ai,
            "count_recovered_baseline": count_rec_baseline,
            "root_cause_breakdown": root_cause_counts,
            "action_breakdown": action_counts,
        }

        return results, summary
