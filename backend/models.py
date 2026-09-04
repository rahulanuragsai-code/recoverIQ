import json
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from backend.database import Base


def get_utc_now():
    return datetime.now(timezone.utc)


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), index=True, nullable=False)
    customer_segment = Column(String(32), nullable=False)  # new, regular, high_value
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="INR", nullable=False)
    gateway = Column(String(64), nullable=False)
    decline_code = Column(String(64), nullable=False)
    decline_message = Column(Text, nullable=False)
    timestamp = Column(String(64), nullable=False)
    is_subscription = Column(Boolean, default=False, nullable=False)
    previous_retry_count = Column(Integer, default=0, nullable=False)
    fraud_flag = Column(Boolean, default=False, nullable=False)
    is_synthetic = Column(Boolean, default=True, nullable=False)
    edge_case_tag = Column(String(64), nullable=True)

    # Pipeline Analysis Results
    root_cause = Column(String(64), nullable=True)
    root_cause_rationale = Column(Text, nullable=True)
    recoverability_score = Column(Float, nullable=True)
    score_factors = Column(Text, nullable=True)  # JSON list of factors

    # Proposed LLM Strategy
    proposed_action = Column(String(64), nullable=True)
    proposed_playbook = Column(Text, nullable=True)  # JSON dict

    # Deterministic Policy Gate
    policy_gate_verdict = Column(String(32), nullable=True)  # PASSED or OVERRIDDEN
    policy_overrides = Column(Text, nullable=True)  # JSON list of rules fired
    final_action = Column(String(64), nullable=True)
    final_playbook = Column(Text, nullable=True)  # JSON dict

    # Outcome Simulation
    simulated_outcome_ai = Column(String(32), nullable=True)  # RECOVERED, FAILED, SKIPPED
    simulated_retries_ai = Column(Integer, default=0)
    simulated_outcome_baseline = Column(String(32), nullable=True)  # RECOVERED, FAILED
    simulated_retries_baseline = Column(Integer, default=0)
    false_retry_avoided = Column(Boolean, default=False)
    analyzed_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "transaction_id": self.transaction_id,
            "customer_id": self.customer_id,
            "customer_segment": self.customer_segment,
            "amount": self.amount,
            "currency": self.currency,
            "gateway": self.gateway,
            "decline_code": self.decline_code,
            "decline_message": self.decline_message,
            "timestamp": self.timestamp,
            "is_subscription": self.is_subscription,
            "previous_retry_count": self.previous_retry_count,
            "fraud_flag": self.fraud_flag,
            "is_synthetic": self.is_synthetic,
            "edge_case_tag": self.edge_case_tag,
            "root_cause": self.root_cause,
            "root_cause_rationale": self.root_cause_rationale,
            "recoverability_score": self.recoverability_score,
            "score_factors": json.loads(self.score_factors) if self.score_factors else [],
            "proposed_action": self.proposed_action,
            "proposed_playbook": json.loads(self.proposed_playbook) if self.proposed_playbook else None,
            "policy_gate_verdict": self.policy_gate_verdict,
            "policy_overrides": json.loads(self.policy_overrides) if self.policy_overrides else [],
            "final_action": self.final_action,
            "final_playbook": json.loads(self.final_playbook) if self.final_playbook else None,
            "simulated_outcome_ai": self.simulated_outcome_ai,
            "simulated_retries_ai": self.simulated_retries_ai,
            "simulated_outcome_baseline": self.simulated_outcome_baseline,
            "simulated_retries_baseline": self.simulated_retries_baseline,
            "false_retry_avoided": self.false_retry_avoided,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
        }


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(64), index=True, nullable=False)
    customer_id = Column(String(64), index=True, nullable=False)
    proposed_action = Column(String(64), nullable=False)
    proposed_playbook = Column(Text, nullable=False)  # JSON
    policy_verdict = Column(String(32), nullable=False)  # PASSED or OVERRIDDEN
    rules_fired = Column(Text, nullable=False)  # JSON list
    override_reasons = Column(Text, nullable=False)  # JSON list
    final_action = Column(String(64), nullable=False)
    final_playbook = Column(Text, nullable=False)  # JSON
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "customer_id": self.customer_id,
            "proposed_action": self.proposed_action,
            "proposed_playbook": json.loads(self.proposed_playbook) if self.proposed_playbook else {},
            "policy_verdict": self.policy_verdict,
            "rules_fired": json.loads(self.rules_fired) if self.rules_fired else [],
            "override_reasons": json.loads(self.override_reasons) if self.override_reasons else [],
            "final_action": self.final_action,
            "final_playbook": json.loads(self.final_playbook) if self.final_playbook else {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SimulationSummary(Base):
    __tablename__ = "simulation_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    seed = Column(Integer, default=42, nullable=False)
    total_transactions = Column(Integer, nullable=False)
    amount_at_risk = Column(Float, nullable=False)
    amount_recovered_ai = Column(Float, nullable=False)
    amount_recovered_baseline = Column(Float, nullable=False)
    recovery_rate_ai = Column(Float, nullable=False)
    recovery_rate_baseline = Column(Float, nullable=False)
    recovery_rate_uplift_pct = Column(Float, nullable=False)
    false_retries_avoided = Column(Integer, nullable=False)
    policy_overrides_count = Column(Integer, nullable=False)
    simulated_at = Column(DateTime, default=get_utc_now, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "seed": self.seed,
            "total_transactions": self.total_transactions,
            "amount_at_risk": self.amount_at_risk,
            "amount_recovered_ai": self.amount_recovered_ai,
            "amount_recovered_baseline": self.amount_recovered_baseline,
            "recovery_rate_ai": self.recovery_rate_ai,
            "recovery_rate_baseline": self.recovery_rate_baseline,
            "recovery_rate_uplift_pct": self.recovery_rate_uplift_pct,
            "false_retries_avoided": self.false_retries_avoided,
            "policy_overrides_count": self.policy_overrides_count,
            "simulated_at": self.simulated_at.isoformat() if self.simulated_at else None,
        }
