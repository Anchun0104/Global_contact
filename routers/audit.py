from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from database import get_db
from models import AuditLog
from schemas import AuditLogResponse
from auth import get_admin_user

router = APIRouter(prefix="/api/audit", tags=["审计日志"])


@router.get("", response_model=dict)
def list_audit_logs(
    action: Optional[str] = Query(None),
    target_type: Optional[str] = Query(None),
    username: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _=Depends(get_admin_user),
):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)
    if username:
        query = query.filter(AuditLog.username.like(f"%{username}%"))

    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = [
        {
            "id": log.id,
            "user_id": log.user_id,
            "username": log.username,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": str(log.created_at) if log.created_at else None,
        }
        for log in logs
    ]
    return {"total": total, "items": items, "page": page, "page_size": page_size}


@router.get("/stats", response_model=list[dict])
def audit_stats(db: Session = Depends(get_db), _=Depends(get_admin_user)):
    type_stats = db.query(
        AuditLog.target_type,
        func.count(AuditLog.id).label("count"),
    ).group_by(AuditLog.target_type).all()

    action_stats = db.query(
        AuditLog.action,
        func.count(AuditLog.id).label("count"),
    ).group_by(AuditLog.action).all()

    return [
        {"type": "by_target", "data": [{"name": t, "value": c} for t, c in type_stats]},
        {"type": "by_action", "data": [{"name": a, "value": c} for a, c in action_stats]},
    ]
