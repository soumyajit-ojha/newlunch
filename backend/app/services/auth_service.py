from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate
from app.core.security import hash_password, create_access_token, verify_password

class AuthService:
    @staticmethod
    def register_user(db: Session, user_in: UserCreate):
        # 1. Check if user exists
        user_exists = UserRepository.get_by_email(db, user_in.email)
        if user_exists:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # 2. Hash password and save
        hashed_pwd = hash_password(user_in.password)
        return UserRepository.create(db, user_in, hashed_pwd)

    @staticmethod
    def login_user(db: Session, email, password):
        user = UserRepository.get_by_email(db, email)
        if not user or not verify_password(password, user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = create_access_token({"sub": user.email, "role": user.role.value})
        return {"access_token": token, "token_type": "bearer", "user_role": user.role.value}