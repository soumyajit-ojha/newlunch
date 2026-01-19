from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, Token, UserLogin
from app.services.auth_service import AuthService
from app.routers.deps import get_current_user
from app.models.user import User
from app.utils.log_config import logger

router = APIRouter()


@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    logger.info("User registration attempt: %s", user_in.email)
    user = AuthService.register_user(db, user_in)
    logger.info("User registered successfully: %s", user_in.email)
    return user


@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    logger.info("User login attempt: %s", user_credentials.email)
    token_data = AuthService.login_user(db, user_credentials.email, user_credentials.password)
    logger.info("User logged in successfully: %s", user_credentials.email)
    return token_data


@router.get("/me", response_model=UserResponse)
def read_user_me(current_user: User = Depends(get_current_user)):
    """
    This route is now PROTECTED.
    If a user doesn't provide a valid token, they get a 401 Unauthorized.
    """
    logger.info("Current user requested: %s", current_user.email)
    return current_user
