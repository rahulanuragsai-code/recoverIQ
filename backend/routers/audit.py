from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import AuditLog
from backend.schemas import AuditLogListResponse, AuditLogSchema

router = APIRouter(prefix="/api/audit-log", tags=["Audit Log"])


@router.get("", response_model=AuditLogListResponse)
def get_audit_logs(
    verdict: Optional[str] = Query(None, description="PASSED | OVERRIDDEN"),
    action: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    transaction_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Paginated, filterable audit trail of decisions, LLM proposals, policy gate verdicts, and overrides.
    """
    query = db.query(AuditLog)

    if verdict:
        query = query.filter(AuditLog.policy_verdict == verdict)
    if action:
        query = query.filter(AuditLog.final_action == action)
    if customer_id:
        query = query.filter(AuditLog.customer_id == customer_id)
    if transaction_id:
        query = query.filter(AuditLog.transaction_id == transaction_id)
    if search:
        s = f"%{search}%"
        query = query.filter(
            (AuditLog.transaction_id.ilike(s))
            | (AuditLog.customer_id.ilike(s))
            | (AuditLog.rules_fired.ilike(s))
            | (AuditLog.override_reasons.ilike(s))
            | (AuditLog.proposed_action.ilike(s))
            | (AuditLog.final_action.ilike(s))
        )

    total = query.count()
    logs = query.order_by(AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

    log_schemas = [AuditLogSchema.model_validate(log.to_dict()) for log in logs]

    return AuditLogListResponse(
        total=total,
        page=page,
        page_size=page_size,
        logs=log_schemas,
    )
