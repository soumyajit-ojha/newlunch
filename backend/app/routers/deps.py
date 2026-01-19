from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.repositories.user_repo import UserRepository
from app.models.user import User, UserRole
from app.utils.log_config import logger

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
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            logger.warning("JWT validation failed: missing sub")
            raise credentials_exception
    except JWTError as e:
        logger.warning("JWT validation failed: %s", e)
        raise credentials_exception

    user = UserRepository.get_by_email(db, email=email)

    if user is None:
        logger.warning("JWT valid but user not found: email=%s", email)
        raise credentials_exception

    if not user.is_active:
        logger.warning("Inactive user attempted access: email=%s", email)
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


# --- Role Based Access Control (RBAC) Helpers ---


def get_current_active_seller(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensures the user is a SELLER"""
    if current_user.role != UserRole.SELLER:
        logger.warning("Seller role required: user_id=%s role=%s", current_user.id, current_user.role)
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
        logger.warning("Admin role required: user_id=%s role=%s", current_user.id, current_user.role)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user

