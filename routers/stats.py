from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import Professor, Conference, Cooperation, SubConference, SubConfStatus, AuditLog, User
from auth import get_current_user, get_admin_user

router = APIRouter(prefix="/api/stats", tags=["统计"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _=Depends(get_current_user)):
    total_professors = db.query(func.count(Professor.id)).scalar()
    total_conferences = db.query(func.count(Conference.id)).scalar()
    total_cooperations = db.query(func.count(Cooperation.id)).scalar()
    total_subconferences = db.query(func.count(SubConference.id)).scalar()
    unassigned = db.query(func.count(SubConference.id)).filter(
        SubConference.status == SubConfStatus.PENDING
    ).scalar()

    direction_dist = db.query(
        Professor.research_direction,
        func.count(Professor.id).label("count"),
    ).filter(Professor.research_direction.isnot(None)).group_by(Professor.research_direction).all()
    direction_distribution = [{"name": d, "value": c} for d, c in direction_dist]

    coop_type_dist = db.query(
        Cooperation.cooperation_type,
        func.count(Cooperation.id).label("count"),
    ).group_by(Cooperation.cooperation_type).all()
    cooperation_type_distribution = [{"name": t.value if hasattr(t, 'value') else t, "value": c} for t, c in coop_type_dist]

    top = db.query(
        Professor.id,
        Professor.name,
        func.count(Cooperation.id).label("count"),
    ).join(Cooperation, Professor.id == Cooperation.professor_id).group_by(Professor.id).order_by(
        func.count(Cooperation.id).desc()
    ).limit(10).all()
    top_professors = [{"id": p_id, "name": p_name, "count": c} for p_id, p_name, c in top]

    conf_progress = db.query(
        Conference.id,
        Conference.name,
        func.count(SubConference.id).label("total"),
        func.count(SubConference.id).filter(SubConference.status != SubConfStatus.PENDING).label("assigned"),
    ).outerjoin(SubConference, Conference.id == SubConference.conference_id).group_by(Conference.id).all()
    conference_progress = [
        {"id": cid, "name": cname, "total": t, "assigned": a}
        for cid, cname, t, a in conf_progress
    ]

    return {
        "total_professors": total_professors,
        "total_conferences": total_conferences,
        "total_cooperations": total_cooperations,
        "total_subconferences": total_subconferences,
        "unassigned_subconferences": unassigned,
        "direction_distribution": direction_distribution,
        "cooperation_type_distribution": cooperation_type_distribution,
        "top_professors": top_professors,
        "conference_progress": conference_progress,
    }


@router.get("/professor/{professor_id}/recommended_conferences")
def recommended_conferences(professor_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    p = db.query(Professor).filter(Professor.id == professor_id).first()
    if not p:
        return []
    if not p.research_direction:
        return []

    already_cooperated = db.query(Cooperation.conference_id).filter(
        Cooperation.professor_id == professor_id
    ).subquery()

    recommendations = db.query(Conference).filter(
        Conference.field == p.research_direction,
        Conference.id.notin_(already_cooperated),
    ).order_by(Conference.year.desc()).all()

    return [
        {
            "id": c.id,
            "name": c.name,
            "year": c.year,
            "field": c.field,
            "status": c.status.value if c.status else None,
        }
        for c in recommendations
    ]


@router.get("/user-workload")
def user_workload(db: Session = Depends(get_db), _=Depends(get_admin_user)):
    users = db.query(User).order_by(User.id).all()
    result = []
    for u in users:
        base = db.query(AuditLog).filter(AuditLog.user_id == u.id)
        total_ops = base.count()
        create_count = base.filter(AuditLog.action == "create").count()
        update_count = base.filter(AuditLog.action == "update").count()
        delete_count = base.filter(AuditLog.action == "delete").count()
        professor_count = base.filter(AuditLog.target_type == "professor", AuditLog.action == "create").count()
        conference_count = base.filter(AuditLog.target_type == "conference", AuditLog.action == "create").count()
        cooperation_count = base.filter(AuditLog.target_type == "cooperation", AuditLog.action == "create").count()
        result.append({
            "user_id": u.id,
            "username": u.username,
            "display_name": u.display_name or u.username,
            "total_operations": total_ops,
            "create_count": create_count,
            "update_count": update_count,
            "delete_count": delete_count,
            "professor_count": professor_count,
            "conference_count": conference_count,
            "cooperation_count": cooperation_count,
        })
    return result


@router.get("/conference/{conference_id}/potential_professors")
def potential_professors(conference_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    conf = db.query(Conference).filter(Conference.id == conference_id).first()
    if not conf:
        return []
    if not conf.field:
        return []

    already_cooperated = db.query(Cooperation.professor_id).filter(
        Cooperation.conference_id == conference_id
    ).subquery()

    potentials = db.query(Professor).filter(
        Professor.research_direction == conf.field,
        Professor.id.notin_(already_cooperated),
    ).order_by(Professor.qs_ranking).all()

    return [
        {
            "id": p.id,
            "name": p.name,
            "title": p.title,
            "university": p.university,
            "qs_ranking": p.qs_ranking,
            "research_direction": p.research_direction,
        }
        for p in potentials
    ]
