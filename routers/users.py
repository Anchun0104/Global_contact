from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import UserCreate, UserUpdate, UserResetPassword, UserResponse
from auth import hash_password, get_admin_user, get_current_user

router = APIRouter(prefix="/api/users", tags=["用户管理"])


@router.get("", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), _=Depends(get_admin_user)):
    users = db.query(User).order_by(User.id).all()
    return users


@router.post("", response_model=UserResponse)
def create_user(data: UserCreate, db: Session = Depends(get_db), _=Depends(get_admin_user)):
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        display_name=data.display_name or data.username,
        role=data.role if data.role in ("admin", "user") else "user",
        is_active=1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), _=Depends(get_admin_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if data.display_name is not None:
        user.display_name = data.display_name
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = 1 if data.is_active else 0
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), _=Depends(get_admin_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.username == "admin":
        raise HTTPException(status_code=400, detail="不能删除管理员账户")
    db.delete(user)
    db.commit()
    return {"message": "用户已删除"}


@router.post("/{user_id}/reset-password")
def reset_password(user_id: int, data: UserResetPassword, db: Session = Depends(get_db), _=Depends(get_admin_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "密码已重置"}


@router.post("/me/password")
def change_own_password(data: UserResetPassword, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "密码已修改"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "display_name": current_user.display_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
    }
