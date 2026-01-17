from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, Token, UserLogin
from app.services.auth_service import AuthService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    print("Input Data", str(user_in))
    return AuthService.register_user(db, user_in)


@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    print("Input Data", str(user_credentials))
    return AuthService.login_user(db, user_credentials.email, user_credentials.password)


@router.get("/me", response_model=UserResponse)
def read_user_me(current_user: User = Depends(get_current_user)):
    """
    This route is now PROTECTED.
    If a user doesn't provide a valid token, they get a 401 Unauthorized.
    """
    return current_user
