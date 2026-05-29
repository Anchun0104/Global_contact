from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import ResearchDirection, Professor, User
from schemas import DirectionCreate
from auth import get_current_user, log_audit

router = APIRouter(prefix="/api/directions", tags=["研究方向"])


@router.get("")
def list_directions(db: Session = Depends(get_db), _=Depends(get_current_user)):
    items = db.query(ResearchDirection).order_by(ResearchDirection.name).all()
    return [{"id": d.id, "name": d.name} for d in items]


@router.post("")
def create_direction(data: DirectionCreate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(ResearchDirection).filter(ResearchDirection.name == data.name).first()
    if existing:
        return {"id": existing.id, "name": existing.name}
    d = ResearchDirection(name=data.name)
    db.add(d)
    db.commit()
    db.refresh(d)
    log_audit(db, current_user, "create", "direction", d.id, f"新增研究方向: {d.name}", request)
    return {"id": d.id, "name": d.name}


@router.delete("/{direction_id}")
def delete_direction(direction_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    d = db.query(ResearchDirection).filter(ResearchDirection.id == direction_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="研究方向不存在")
    count = db.query(Professor).filter(Professor.research_direction == d.name).count()
    if count > 0:
        raise HTTPException(status_code=400, detail=f"还有 {count} 位教授使用此方向，无法删除")
    name = d.name
    db.delete(d)
    db.commit()
    log_audit(db, current_user, "delete", "direction", direction_id, f"删除研究方向: {name}", request)
    return {"message": "删除成功"}


@router.get("/suggestions")
def get_suggestions(db: Session = Depends(get_db), _=Depends(get_current_user)):
    used = db.query(Professor.research_direction).distinct().filter(Professor.research_direction.isnot(None)).all()
    predefined = db.query(ResearchDirection.name).all()
    names = set()
    for (n,) in used:
        if n:
            names.add(n)
    for (n,) in predefined:
        if n:
            names.add(n)
    return sorted(list(names))
