"""
Pluggable LLM Client for RecoverIQ.
Automatically falls back to a deterministic Mock LLM if no API key is provided
or if LLM_MODE=mock, ensuring zero external dependencies by default.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict
import httpx
from backend.config import settings

logger = logging.getLogger("recoveriq.llm")


class BaseLLMClient(ABC):
    @abstractmethod
    def classify_root_cause(self, decline_code: str, decline_message: str) -> Dict[str, str]:
        """Classify ambiguous decline message into a canonical root cause with rationale."""
        pass

    @abstractmethod
    def generate_playbook(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Propose recovery playbook JSON based on transaction context."""
        pass


class MockLLMClient(BaseLLMClient):
    """
    Deterministic mock LLM providing realistic reasoning and structured JSON.
    Guarantees 100% reproducible results without internet access or API keys.
    """

    def classify_root_cause(self, decline_code: str, decline_message: str) -> Dict[str, str]:
        msg = decline_message.lower()
        code = decline_code.upper()

        if any(term in msg for term in ["fraud", "risk", "watchlist", "intercepted", "blocked by risk"]):
            return {
                "root_cause": "SUSPECTED_FRAUD",
                "rationale": "High-risk signals and risk-engine triggers detected in gateway response message.",
            }
        elif any(term in msg for term in ["balance", "funds", "depleted", "ceiling", "exceeded", "code 51"]):
            return {
                "root_cause": "INSUFFICIENT_FUNDS",
                "rationale": "Gateway payload indicates customer account lacks adequate funds or reached debit limit.",
            }
        elif any(term in msg for term in ["expired", "validity", "plastic", "code 54"]):
            return {
                "root_cause": "CARD_EXPIRED",
                "rationale": "Card instrument validity window has lapsed according to issuer response.",
            }
        elif any(term in msg for term in ["cvv", "security code", "cvc", "code 82"]):
            return {
                "root_cause": "INVALID_CVV",
                "rationale": "Card security verification value failed validation against card network records.",
            }
        elif any(term in msg for term in ["timeout", "timed out", "unresponsive", "connection", "switch ping", "code 91"]):
            return {
                "root_cause": "NETWORK_TIMEOUT",
                "rationale": "Transient network communication breakdown between acquirer switch and issuer banking host.",
            }
        elif any(term in msg for term in ["processor", "database constraint", "malfunction", "code 96"]):
            return {
                "root_cause": "PROCESSING_ERROR",
                "rationale": "Transient internal host processing failure at the payment processor or switch.",
            }
        else:
            return {
                "root_cause": code if code in [
                    "INSUFFICIENT_FUNDS", "CARD_EXPIRED", "ISSUER_DECLINE",
                    "INVALID_CVV", "NETWORK_TIMEOUT", "SUSPECTED_FRAUD", "PROCESSING_ERROR"
                ] else "ISSUER_DECLINE",
                "rationale": "Generic issuer policy decline requiring secondary customer mandate verification.",
            }

    def generate_playbook(self, context: Dict[str, Any]) -> Dict[str, Any]:
        root_cause = context.get("root_cause", "ISSUER_DECLINE")
        score = context.get("recoverability_score", 0.5)
        segment = context.get("customer_segment", "regular")
        prev_retries = context.get("previous_retry_count", 0)
        is_sub = context.get("is_subscription", False)
        edge_tag = context.get("edge_case_tag")

        # Edge Case 2: Expired card with secondary UPI mandate in customer wallet
        if edge_tag == "expired_card_backup_mandate":
            return {
                "action": "notify_customer",
                "channel": "whatsapp",
                "retry_delay_hours": 0,
                "max_retries": 0,
                "rationale": "Primary card expired but customer has linked UPI Autopay. Trigger WhatsApp 1-click fallback notification to switch mandate without blind gateway retries.",
            }

        # Fraud cases
        if root_cause == "SUSPECTED_FRAUD":
            return {
                "action": "escalate_human",
                "channel": "none",
                "retry_delay_hours": 0,
                "max_retries": 0,
                "rationale": "Suspected fraudulent activity flagged. Halting automated recovery; manual security review mandated.",
            }

        # Expired cards
        if root_cause == "CARD_EXPIRED":
            channel = "whatsapp" if segment == "high_value" else "email"
            return {
                "action": "notify_customer",
                "channel": channel,
                "retry_delay_hours": 0,
                "max_retries": 0,
                "rationale": "Card expired. Automated retries will fail; prompting customer to update card details in-app/via link.",
            }

        # Invalid CVV
        if root_cause == "INVALID_CVV":
            return {
                "action": "notify_customer",
                "channel": "sms" if segment == "new" else "in_app",
                "retry_delay_hours": 0,
                "max_retries": 0,
                "rationale": "Incorrect CVV provided. Halting automatic retries to prevent card lockout; requesting customer re-entry.",
            }

        # Network Timeout or Processing Error
        if root_cause in ["NETWORK_TIMEOUT", "PROCESSING_ERROR"]:
            if prev_retries == 0:
                return {
                    "action": "retry_now",
                    "channel": "none",
                    "retry_delay_hours": 0,
                    "max_retries": 1,
                    "rationale": "Transient network or switch timeout. High likelihood of immediate recovery upon instant re-attempt.",
                }
            else:
                return {
                    "action": "retry_scheduled",
                    "channel": "none",
                    "retry_delay_hours": 12,
                    "max_retries": 1,
                    "rationale": "Repeat infrastructure failure. Delaying retry by 12h to allow switch recovery.",
                }

        # Insufficient Funds
        if root_cause == "INSUFFICIENT_FUNDS":
            if prev_retries >= 2:
                return {
                    "action": "notify_customer",
                    "channel": "whatsapp" if segment == "high_value" else "email",
                    "retry_delay_hours": 0,
                    "max_retries": 0,
                    "rationale": "Repeated insufficient funds declines. Direct customer alert advised before final retry.",
                }
            delay = 24 if segment == "high_value" else 48
            channel = "whatsapp" if segment == "high_value" else "sms"
            return {
                "action": "retry_scheduled",
                "channel": channel,
                "retry_delay_hours": delay,
                "max_retries": 1,
                "rationale": f"Scheduled retry delayed by {delay} hours to align with expected balance replenishment, with {channel} nudge.",
            }

        # Generic Issuer Decline
        if is_sub and segment == "high_value":
            return {
                "action": "retry_scheduled",
                "channel": "in_app",
                "retry_delay_hours": 24,
                "max_retries": 1,
                "rationale": "High-value recurring subscription. Scheduled retry in 24h with in-app banner for mandate re-authorization.",
            }
        elif prev_retries >= 2:
            return {
                "action": "escalate_human",
                "channel": "none",
                "retry_delay_hours": 0,
                "max_retries": 0,
                "rationale": "Multiple issuer declines with exhausted attempts. Flagged for merchant finance-ops team.",
            }
        else:
            return {
                "action": "retry_scheduled",
                "channel": "email",
                "retry_delay_hours": 24,
                "max_retries": 1,
                "rationale": "Standard issuer decline. Scheduling 24h cooldown retry with customer notification email.",
            }


class OpenAILLMClient(BaseLLMClient):
    """
    Live LLM client calling any OpenAI-compatible endpoint.
    Falls back gracefully to MockLLMClient if an error occurs.
    """

    def __init__(self):
        self.fallback = MockLLMClient()
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL.rstrip("/")
        self.model = settings.OPENAI_MODEL

    def classify_root_cause(self, decline_code: str, decline_message: str) -> Dict[str, str]:
        if not self.api_key:
            return self.fallback.classify_root_cause(decline_code, decline_message)

        prompt = f"""You are a payment failure diagnostic engine.
Classify this payment failure into exactly one root cause:
Available root causes: [INSUFFICIENT_FUNDS, CARD_EXPIRED, ISSUER_DECLINE, INVALID_CVV, NETWORK_TIMEOUT, SUSPECTED_FRAUD, PROCESSING_ERROR].

Decline Code: {decline_code}
Decline Message: {decline_message}

Respond ONLY with a JSON object:
{{
  "root_cause": "<one_of_the_above>",
  "rationale": "<one sentence explanation>"
}}
"""
        try:
            with httpx.Client(timeout=8.0) as client:
                resp = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.1,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    if "root_cause" in parsed and "rationale" in parsed:
                        return parsed
        except Exception as e:
            logger.warning("OpenAI API call failed (%s), falling back to deterministic mock.", e)

        return self.fallback.classify_root_cause(decline_code, decline_message)

    def generate_playbook(self, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            return self.fallback.generate_playbook(context)

        prompt = f"""You are an expert revenue recovery AI for a fintech merchant.
Generate an optimal recovery playbook for this failed transaction:

Context:
{json.dumps(context, indent=2)}

Available actions: [retry_now, retry_scheduled, notify_customer, escalate_human, do_not_retry]
Available channels: [email, sms, whatsapp, in_app, none]

Respond ONLY with a JSON object:
{{
  "action": "<action>",
  "channel": "<channel>",
  "retry_delay_hours": <int>,
  "max_retries": <int>,
  "rationale": "<one sentence justification>"
}}
"""
        try:
            with httpx.Client(timeout=8.0) as client:
                resp = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.1,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    required_keys = ["action", "channel", "retry_delay_hours", "max_retries", "rationale"]
                    if all(k in parsed for k in required_keys):
                        return parsed
        except Exception as e:
            logger.warning("OpenAI strategy generation failed (%s), falling back to mock.", e)

        return self.fallback.generate_playbook(context)


def get_llm_client() -> BaseLLMClient:
    """Factory to retrieve configured LLM client."""
    if settings.LLM_MODE == "live" and settings.OPENAI_API_KEY:
        return OpenAILLMClient()
    return MockLLMClient()
