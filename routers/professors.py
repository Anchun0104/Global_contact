from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from database import get_db
from models import Professor, Cooperation, ResearchDirection, User
from schemas import ProfessorCreate, ProfessorUpdate, ProfessorResponse
from auth import get_current_user, log_audit

router = APIRouter(prefix="/api/professors", tags=["教授管理"])


def _professor_to_response(p, cooperation_count=None):
    data = {
        "id": p.id,
        "name": p.name,
        "title": p.title,
        "university": p.university,
        "email": p.email,
        "website": p.website,
        "location": p.location,
        "qs_ranking": p.qs_ranking,
        "research_direction": p.research_direction,
        "research_keywords": p.research_keywords,
        "notes": p.notes,
        "created_at": p.created_at,
        "updated_at": p.updated_at,
        "cooperation_count": cooperation_count,
    }
    return ProfessorResponse(**data)


@router.get("")
def list_professors(
    search: Optional[str] = Query(None),
    direction: Optional[str] = Query(None),
    university: Optional[str] = Query(None),
    qs_min: Optional[int] = Query(None),
    qs_max: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    query = db.query(Professor)
    if search:
        like = f"%{search}%"
        query = query.filter(
            Professor.name.like(like)
            | Professor.university.like(like)
            | Professor.research_direction.like(like)
        )
    if direction:
        query = query.filter(Professor.research_direction == direction)
    if university:
        query = query.filter(Professor.university.like(f"%{university}%"))
    if qs_min is not None:
        query = query.filter(Professor.qs_ranking >= qs_min)
    if qs_max is not None:
        query = query.filter(Professor.qs_ranking <= qs_max)

    total = query.count()
    professors = query.order_by(Professor.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for p in professors:
        count = db.query(func.count(Cooperation.id)).filter(Cooperation.professor_id == p.id).scalar()
        result.append(_professor_to_response(p, count))

    return {"total": total, "items": result, "page": page, "page_size": page_size}


@router.get("/{professor_id}")
def get_professor(professor_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    p = db.query(Professor).filter(Professor.id == professor_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="教授不存在")
    count = db.query(func.count(Cooperation.id)).filter(Cooperation.professor_id == p.id).scalar()
    return _professor_to_response(p, count)


@router.post("")
def create_professor(data: ProfessorCreate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    p = Professor(**data.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    if data.research_direction:
        existing = db.query(ResearchDirection).filter(ResearchDirection.name == data.research_direction).first()
        if not existing:
            db.add(ResearchDirection(name=data.research_direction))
            db.commit()
    log_audit(db, current_user, "create", "professor", p.id, f"新增教授: {p.name}", request)
    return _professor_to_response(p, 0)


@router.put("/{professor_id}")
def update_professor(professor_id: int, data: ProfessorUpdate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    p = db.query(Professor).filter(Professor.id == professor_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="教授不存在")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(p, key, val)
    db.commit()
    db.refresh(p)
    if data.research_direction:
        existing = db.query(ResearchDirection).filter(ResearchDirection.name == data.research_direction).first()
        if not existing:
            db.add(ResearchDirection(name=data.research_direction))
            db.commit()
    log_audit(db, current_user, "update", "professor", p.id, f"修改教授: {p.name}", request)
    count = db.query(func.count(Cooperation.id)).filter(Cooperation.professor_id == p.id).scalar()
    return _professor_to_response(p, count)


@router.delete("/{professor_id}")
def delete_professor(professor_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    p = db.query(Professor).filter(Professor.id == professor_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="教授不存在")
    name = p.name
    db.delete(p)
    db.commit()
    log_audit(db, current_user, "delete", "professor", professor_id, f"删除教授: {name}", request)
    return {"message": "删除成功"}
