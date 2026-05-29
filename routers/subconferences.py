from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from database import get_db
from models import SubConference, Cooperation, Professor, Conference, SubConfStatus, User
from schemas import SubConferenceCreate, SubConferenceUpdate
from auth import get_current_user, log_audit

router = APIRouter(prefix="/api/subconferences", tags=["分会场管理"])


@router.get("")
def list_subconferences(
    conference_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    query = db.query(SubConference)
    if conference_id:
        query = query.filter(SubConference.conference_id == conference_id)
    if status:
        query = query.filter(SubConference.status == status)
    items = query.order_by(SubConference.id).all()
    result = []
    for s in items:
        coop = db.query(Cooperation).filter(Cooperation.sub_conference_id == s.id).first()
        assigned = None
        coop_type = None
        if coop:
            p = db.query(Professor).filter(Professor.id == coop.professor_id).first()
            if p:
                assigned = {
                    "id": p.id,
                    "name": p.name,
                    "title": p.title,
                    "university": p.university,
                    "research_direction": p.research_direction,
                }
            coop_type = coop.cooperation_type.value if coop.cooperation_type else None
        result.append({
            "id": s.id,
            "conference_id": s.conference_id,
            "name": s.name,
            "description": s.description,
            "field": s.field,
            "status": s.status.value if s.status else None,
            "assigned_professor": assigned,
            "cooperation_type": coop_type,
        })
    return result


@router.post("")
def create_subconference(data: SubConferenceCreate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conf = db.query(Conference).filter(Conference.id == data.conference_id).first()
    if not conf:
        raise HTTPException(status_code=404, detail="会议不存在")
    s = SubConference(**data.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    log_audit(db, current_user, "create", "subconference", s.id, f"新增分会场: {s.name} (会议: {conf.name})", request)
    return {
        "id": s.id,
        "conference_id": s.conference_id,
        "name": s.name,
        "description": s.description,
        "field": s.field,
        "status": s.status.value if s.status else None,
    }


@router.put("/{subconference_id}")
def update_subconference(subconference_id: int, data: SubConferenceUpdate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    s = db.query(SubConference).filter(SubConference.id == subconference_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="分会场不存在")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(s, key, val)
    db.commit()
    db.refresh(s)
    log_audit(db, current_user, "update", "subconference", s.id, f"修改分会场: {s.name}", request)
    return {
        "id": s.id,
        "conference_id": s.conference_id,
        "name": s.name,
        "description": s.description,
        "field": s.field,
        "status": s.status.value if s.status else None,
    }


@router.delete("/{subconference_id}")
def delete_subconference(subconference_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    s = db.query(SubConference).filter(SubConference.id == subconference_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="分会场不存在")
    name = s.name
    db.query(Cooperation).filter(Cooperation.sub_conference_id == subconference_id).delete()
    db.delete(s)
    db.commit()
    log_audit(db, current_user, "delete", "subconference", subconference_id, f"删除分会场: {name}", request)
    return {"message": "删除成功"}


@router.post("/{subconference_id}/assign")
def assign_professor(
    subconference_id: int,
    request: Request,
    professor_id: int = Query(...),
    cooperation_type: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = db.query(SubConference).filter(SubConference.id == subconference_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="分会场不存在")
    p = db.query(Professor).filter(Professor.id == professor_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="教授不存在")

    existing = db.query(Cooperation).filter(Cooperation.sub_conference_id == subconference_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="该分会场已分配教授，请先取消原分配")

    coop = Cooperation(
        professor_id=professor_id,
        conference_id=s.conference_id,
        sub_conference_id=subconference_id,
        cooperation_type=cooperation_type,
    )
    db.add(coop)
    s.status = SubConfStatus.ASSIGNED
    db.commit()
    log_audit(db, current_user, "create", "cooperation", coop.id, f"分配教授 {p.name} 到分会场: {s.name}", request)
    return {"message": "分配成功"}


@router.post("/{subconference_id}/unassign")
def unassign_professor(subconference_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    s = db.query(SubConference).filter(SubConference.id == subconference_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="分会场不存在")
    db.query(Cooperation).filter(Cooperation.sub_conference_id == subconference_id).delete()
    s.status = SubConfStatus.PENDING
    db.commit()
    log_audit(db, current_user, "delete", "cooperation", None, f"取消分配分会场: {s.name}", request)
    return {"message": "已取消分配"}
