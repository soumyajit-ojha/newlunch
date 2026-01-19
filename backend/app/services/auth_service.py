from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate
from app.models.user import Profile
from app.core.security import hash_password, create_access_token, verify_password
from app.utils.log_config import logger


class AuthService:
    @staticmethod
    def register_user(db: Session, user_in: UserCreate):
        # 1. Check if user exists
        user_exists = UserRepository.get_by_email(db, user_in.email)
        if user_exists:
            logger.warning(f"{user_exists.email}, already registed")
            raise HTTPException(status_code=400, detail="Email already registered")

        # 2. Hash password and save
        hashed_pwd = hash_password(user_in.password)
        new_user = UserRepository.create(db, user_in, hashed_pwd)
        db_profile = Profile(user_id=new_user.id)
        db.add(db_profile)
        db.commit()
        logger.info("User created: email=%s id=%s", new_user.email, new_user.id)
        return new_user

    @staticmethod
    def login_user(db: Session, email, password):
        user = UserRepository.get_by_email(db, email)
        if not user or not verify_password(password, user.password):
            logger.warning("Invalid credentials")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token({"sub": user.email, "role": user.role.value})
        logger.info("Login success: email=%s role=%s", user.email, user.role.value)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_role": user.role.value,
        }
