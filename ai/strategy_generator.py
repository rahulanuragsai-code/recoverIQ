"""
RecoverIQ - Pipeline Step 3: Strategy Generator
Agentic step where the LLM synthesizes classification, score, factors, and transaction context
to propose an optimal recovery playbook.
"""

from typing import Any, Dict
from ai.llm_client import BaseLLMClient, get_llm_client


class StrategyGenerator:
    def __init__(self, llm_client: BaseLLMClient = None):
        self.llm_client = llm_client or get_llm_client()

    def generate_strategy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesizes transaction context and calls LLM to generate a recovery playbook proposal.
        """
        playbook = self.llm_client.generate_playbook(context)

        # Basic structural validation
        action = playbook.get("action", "retry_scheduled")
        if action not in ["retry_now", "retry_scheduled", "notify_customer", "escalate_human", "do_not_retry"]:
            action = "retry_scheduled"

        channel = playbook.get("channel", "email")
        if channel not in ["email", "sms", "whatsapp", "in_app", "none"]:
            channel = "email"

        retry_delay_hours = int(playbook.get("retry_delay_hours", 0))
        max_retries = int(playbook.get("max_retries", 1))
        rationale = playbook.get("rationale", "Proposed automated recovery strategy based on root cause analysis.")

        return {
            "action": action,
            "channel": channel,
            "retry_delay_hours": retry_delay_hours,
            "max_retries": max_retries,
            "rationale": rationale,
        }
