from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.repositories.user_repo import UserRepository
from app.models.user import User, UserRole

# This tells FastAPI to look for a 'Bearer' token in the Authorization header
security = HTTPBearer()


def get_current_user(
    db: Session = Depends(get_db),
    auth: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    token = auth.credentials    # This automatically extracts the string from 'Bearer <token>'
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 1. Decode JWT
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # 2. Fetch user from DB
    user = UserRepository.get_by_email(db, email=email)

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


# --- Role Based Access Control (RBAC) Helpers ---


def get_current_active_seller(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensures the user is a SELLER"""
    if current_user.role != UserRole.SELLER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges (Seller role required)",
        )
    return current_user


def get_current_active_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensures the user is an ADMIN"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user

