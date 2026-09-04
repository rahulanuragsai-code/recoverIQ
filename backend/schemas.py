from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PlaybookSchema(BaseModel):
    action: str = Field(..., description="retry_now | retry_scheduled | notify_customer | escalate_human | do_not_retry")
    channel: str = Field("none", description="email | sms | whatsapp | in_app | none")
    retry_delay_hours: int = Field(0, description="Delay in hours before retry attempt")
    max_retries: int = Field(1, description="Maximum number of retries authorized")
    rationale: str = Field(..., description="Explanation for the recommended strategy")


class PolicyOverrideSchema(BaseModel):
    rule: str
    reason: str
    original_value: Any
    overridden_value: Any


class ScoreFactorSchema(BaseModel):
    factor: str
    impact: float
    description: str


class TransactionSchema(BaseModel):
    transaction_id: str
    customer_id: str
    customer_segment: str
    amount: float
    currency: str
    gateway: str
    decline_code: str
    decline_message: str
    timestamp: str
    is_subscription: bool
    previous_retry_count: int
    fraud_flag: bool
    is_synthetic: bool = True
    edge_case_tag: Optional[str] = None

    root_cause: Optional[str] = None
    root_cause_rationale: Optional[str] = None
    recoverability_score: Optional[float] = None
    score_factors: Optional[List[ScoreFactorSchema]] = None

    proposed_action: Optional[str] = None
    proposed_playbook: Optional[PlaybookSchema] = None

    policy_gate_verdict: Optional[str] = None
    policy_overrides: Optional[List[PolicyOverrideSchema]] = None
    final_action: Optional[str] = None
    final_playbook: Optional[PlaybookSchema] = None

    simulated_outcome_ai: Optional[str] = None
    simulated_retries_ai: int = 0
    simulated_outcome_baseline: Optional[str] = None
    simulated_retries_baseline: int = 0
    false_retry_avoided: bool = False
    analyzed_at: Optional[str] = None

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    transactions: List[TransactionSchema]


class AuditLogSchema(BaseModel):
    id: int
    transaction_id: str
    customer_id: str
    proposed_action: str
    proposed_playbook: Dict[str, Any]
    policy_verdict: str
    rules_fired: List[str]
    override_reasons: List[str]
    final_action: str
    final_playbook: Dict[str, Any]
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    logs: List[AuditLogSchema]


class SimulationMetricsResponse(BaseModel):
    seed: int
    total_transactions: int
    amount_at_risk: float
    amount_recovered_ai: float
    amount_recovered_baseline: float
    recovery_rate_ai: float
    recovery_rate_baseline: float
    recovery_rate_uplift_pct: float
    false_retries_avoided: int
    policy_overrides_count: int
    simulated_at: Optional[str] = None
    root_cause_breakdown: Optional[Dict[str, int]] = None
    action_breakdown: Optional[Dict[str, int]] = None


class SeedResponse(BaseModel):
    status: str
    count: int
    seed: int
    message: str
