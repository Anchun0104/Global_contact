from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from database import get_db
from models import Conference, SubConference, SubConfStatus, User
from schemas import ConferenceCreate, ConferenceUpdate
from auth import get_current_user, log_audit

router = APIRouter(prefix="/api/conferences", tags=["会议管理"])


@router.get("")
def list_conferences(
    search: Optional[str] = Query(None),
    field: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    query = db.query(Conference)
    if search:
        like = f"%{search}%"
        query = query.filter(Conference.name.like(like) | Conference.field.like(like))
    if field:
        query = query.filter(Conference.field == field)
    if status:
        query = query.filter(Conference.status == status)
    if year:
        query = query.filter(Conference.year == year)

    total = query.count()
    conferences = query.order_by(Conference.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = []
    for c in conferences:
        total_subs = db.query(func.count(SubConference.id)).filter(SubConference.conference_id == c.id).scalar()
        assigned = db.query(func.count(SubConference.id)).filter(
            SubConference.conference_id == c.id,
            SubConference.status != SubConfStatus.PENDING,
        ).scalar()
        items.append({
            "id": c.id,
            "name": c.name,
            "year": c.year,
            "location": c.location,
            "field": c.field,
            "description": c.description,
            "status": c.status.value if c.status else None,
            "total_sessions": c.total_sessions,
            "notes": c.notes,
            "created_at": str(c.created_at) if c.created_at else None,
            "total_subconferences": total_subs,
            "assigned_subconferences": assigned,
        })
    return {"total": total, "items": items, "page": page, "page_size": page_size}


@router.get("/{conference_id}")
def get_conference(conference_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    c = db.query(Conference).filter(Conference.id == conference_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="会议不存在")
    total_subs = db.query(func.count(SubConference.id)).filter(SubConference.conference_id == c.id).scalar()
    assigned = db.query(func.count(SubConference.id)).filter(
        SubConference.conference_id == c.id,
        SubConference.status != SubConfStatus.PENDING,
    ).scalar()
    return {
        "id": c.id,
        "name": c.name,
        "year": c.year,
        "location": c.location,
        "field": c.field,
        "description": c.description,
        "status": c.status.value if c.status else None,
        "total_sessions": c.total_sessions,
        "notes": c.notes,
        "created_at": str(c.created_at) if c.created_at else None,
        "total_subconferences": total_subs,
        "assigned_subconferences": assigned,
    }


@router.post("")
def create_conference(data: ConferenceCreate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = Conference(**data.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    log_audit(db, current_user, "create", "conference", c.id, f"新增会议: {c.name}", request)
    return {
        "id": c.id,
        "name": c.name,
        "year": c.year,
        "location": c.location,
        "field": c.field,
        "description": c.description,
        "status": c.status.value if c.status else None,
        "total_sessions": c.total_sessions,
        "notes": c.notes,
        "created_at": str(c.created_at) if c.created_at else None,
    }


@router.put("/{conference_id}")
def update_conference(conference_id: int, data: ConferenceUpdate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.query(Conference).filter(Conference.id == conference_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="会议不存在")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(c, key, val)
    db.commit()
    db.refresh(c)
    log_audit(db, current_user, "update", "conference", c.id, f"修改会议: {c.name}", request)
    return {
        "id": c.id,
        "name": c.name,
        "year": c.year,
        "location": c.location,
        "field": c.field,
        "description": c.description,
        "status": c.status.value if c.status else None,
        "total_sessions": c.total_sessions,
        "notes": c.notes,
        "created_at": str(c.created_at) if c.created_at else None,
    }


@router.delete("/{conference_id}")
def delete_conference(conference_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.query(Conference).filter(Conference.id == conference_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="会议不存在")
    name = c.name
    db.delete(c)
    db.commit()
    log_audit(db, current_user, "delete", "conference", conference_id, f"删除会议: {name}", request)
    return {"message": "删除成功"}
