from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import SimulationSummary, Transaction
from backend.schemas import SimulationMetricsResponse

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])


@router.get("", response_model=SimulationMetricsResponse)
def get_metrics(db: Session = Depends(get_db)):
    """
    Get current KPI summary metrics, recovery rates, and baseline comparison.
    """
    latest_sim = db.query(SimulationSummary).order_by(SimulationSummary.id.desc()).first()

    if latest_sim:
        # Collect latest breakdown from transactions
        txs = db.query(Transaction).all()
        root_causes = Counter(t.root_cause or "UNCLASSIFIED" for t in txs)
        actions = Counter(t.final_action or "PENDING" for t in txs)

        return SimulationMetricsResponse(
            seed=latest_sim.seed,
            total_transactions=latest_sim.total_transactions,
            amount_at_risk=latest_sim.amount_at_risk,
            amount_recovered_ai=latest_sim.amount_recovered_ai,
            amount_recovered_baseline=latest_sim.amount_recovered_baseline,
            recovery_rate_ai=latest_sim.recovery_rate_ai,
            recovery_rate_baseline=latest_sim.recovery_rate_baseline,
            recovery_rate_uplift_pct=latest_sim.recovery_rate_uplift_pct,
            false_retries_avoided=latest_sim.false_retries_avoided,
            policy_overrides_count=latest_sim.policy_overrides_count,
            simulated_at=latest_sim.simulated_at.isoformat() if latest_sim.simulated_at else None,
            root_cause_breakdown=dict(root_causes),
            action_breakdown=dict(actions),
        )

    # If no simulation run yet, aggregate baseline stats from current transactions
    txs = db.query(Transaction).all()
    total_amount = sum(t.amount for t in txs)
    root_causes = Counter(t.root_cause or "UNCLASSIFIED" for t in txs)
    actions = Counter(t.final_action or "PENDING" for t in txs)

    return SimulationMetricsResponse(
        seed=42,
        total_transactions=len(txs),
        amount_at_risk=round(total_amount, 2),
        amount_recovered_ai=0.0,
        amount_recovered_baseline=0.0,
        recovery_rate_ai=0.0,
        recovery_rate_baseline=0.0,
        recovery_rate_uplift_pct=0.0,
        false_retries_avoided=0,
        policy_overrides_count=0,
        simulated_at=None,
        root_cause_breakdown=dict(root_causes),
        action_breakdown=dict(actions),
    )
