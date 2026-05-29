from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from database import get_db
from models import Cooperation, Professor, Conference, SubConference, SubConfStatus, User
from schemas import CooperationCreate, CooperationUpdate
from auth import get_current_user, log_audit

router = APIRouter(prefix="/api/cooperations", tags=["合作记录"])


@router.get("")
def list_cooperations(
    professor_id: Optional[int] = Query(None),
    conference_id: Optional[int] = Query(None),
    cooperation_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    query = db.query(Cooperation)
    if professor_id:
        query = query.filter(Cooperation.professor_id == professor_id)
    if conference_id:
        query = query.filter(Cooperation.conference_id == conference_id)
    if cooperation_type:
        query = query.filter(Cooperation.cooperation_type == cooperation_type)

    total = query.count()
    items = query.order_by(Cooperation.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for c in items:
        p = db.query(Professor).filter(Professor.id == c.professor_id).first()
        conf = db.query(Conference).filter(Conference.id == c.conference_id).first()
        sub = None
        if c.sub_conference_id:
            sub = db.query(SubConference).filter(SubConference.id == c.sub_conference_id).first()
        result.append({
            "id": c.id,
            "professor_id": c.professor_id,
            "conference_id": c.conference_id,
            "sub_conference_id": c.sub_conference_id,
            "cooperation_type": c.cooperation_type.value if c.cooperation_type else None,
            "notes": c.notes,
            "created_at": str(c.created_at) if c.created_at else None,
            "professor_name": p.name if p else None,
            "conference_name": conf.name if conf else None,
            "sub_conference_name": sub.name if sub else None,
        })
    return {"total": total, "items": result, "page": page, "page_size": page_size}


@router.post("")
def create_cooperation(data: CooperationCreate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    p = db.query(Professor).filter(Professor.id == data.professor_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="教授不存在")
    c = db.query(Conference).filter(Conference.id == data.conference_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="会议不存在")
    if data.sub_conference_id:
        existing = db.query(Cooperation).filter(Cooperation.sub_conference_id == data.sub_conference_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="该分会场已有合作记录")

    coop = Cooperation(**data.model_dump())
    db.add(coop)
    db.commit()
    db.refresh(coop)
    log_audit(db, current_user, "create", "cooperation", coop.id, f"新增合作: {p.name} → {c.name}", request)
    return {"message": "创建成功", "id": coop.id}


@router.put("/{cooperation_id}")
def update_cooperation(cooperation_id: int, data: CooperationUpdate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    coop = db.query(Cooperation).filter(Cooperation.id == cooperation_id).first()
    if not coop:
        raise HTTPException(status_code=404, detail="合作记录不存在")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(coop, key, val)
    db.commit()
    log_audit(db, current_user, "update", "cooperation", cooperation_id, f"修改合作记录 #{cooperation_id}", request)
    return {"message": "更新成功"}


@router.delete("/{cooperation_id}")
def delete_cooperation(cooperation_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    coop = db.query(Cooperation).filter(Cooperation.id == cooperation_id).first()
    if not coop:
        raise HTTPException(status_code=404, detail="合作记录不存在")
    sub_id = coop.sub_conference_id
    db.delete(coop)
    if sub_id:
        sub = db.query(SubConference).filter(SubConference.id == sub_id).first()
        if sub:
            sub.status = SubConfStatus.PENDING
            db.commit()
    db.commit()
    log_audit(db, current_user, "delete", "cooperation", cooperation_id, f"删除合作记录 #{cooperation_id}", request)
    return {"message": "删除成功"}
