from sqlalchemy.orm import Session
from app.models.user import User, Profile, Address
from app.schemas.user import UserCreate, AddressCreate


class UserRepository:
    @staticmethod
    def get_by_email(db: Session, email: str) -> User:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create(db: Session, user_in: UserCreate, hashed_password: str) -> User:
        db_user = User(
            email=user_in.email,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            phone=user_in.phone,
            password=hashed_password,
            role=user_in.role,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def get_profile(db: Session, user_id: int):
        return db.query(Profile).filter(Profile.user_id == user_id).first()

    @staticmethod
    def update_profile(
        db: Session, user_id: int, gender: str = None, pic_url: str = None
    ):
        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        if gender:
            profile.gender = gender
        if pic_url:
            profile.profile_picture = pic_url
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def add_address(db: Session, user_id: int, addr_in: AddressCreate):
        db_addr = Address(**addr_in.model_dump(), user_id=user_id)
        db.add(db_addr)
        db.commit()
        db.refresh(db_addr)
        return db_addr
