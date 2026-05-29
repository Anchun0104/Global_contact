from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import LoginRequest, TokenResponse
from auth import verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="该账号已被禁用",
        )
    token = create_access_token({
        "sub": user.username,
        "role": user.role,
        "display_name": user.display_name or user.username,
    })
    return TokenResponse(
        access_token=token,
        username=user.username,
        role=user.role,
        display_name=user.display_name or user.username,
    )


@router.get("/check")
def check_auth(db: Session = Depends(get_db)):
    return {"status": "ok"}
