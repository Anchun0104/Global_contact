import hashlib
import secrets
import os
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import User

SECRET_KEY = os.getenv("SECRET_KEY", "professor-db-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256(salt.encode() + password.encode()).hexdigest()
    return f"{salt}:{h}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    parts = hashed_password.split(":")
    if len(parts) != 2:
        return False
    salt, h = parts
    return hashlib.sha256(salt.encode() + plain_password.encode()).hexdigest() == h


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
        )
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
        )
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )
    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可执行此操作",
        )
    return current_user


def log_audit(db: Session, user: User, action: str, target_type: str, target_id: int = None, details: str = None, request: Request = None):
    from models import AuditLog
    ip = request.client.host if request and request.client else None
    log = AuditLog(
        user_id=user.id,
        username=user.username,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip,
    )
    db.add(log)
    db.commit()


def init_admin_user(db: Session):
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        admin = User(
            username="admin",
            password_hash=hash_password(admin_password),
            display_name="管理员",
            role="admin",
        )
        db.add(admin)
        db.commit()
