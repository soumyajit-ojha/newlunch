from sqlalchemy.orm import Session, joinedload
from app.models.user import User, Profile, Address
from app.schemas.user import UserCreate, AddressCreate
from app.utils.log_config import logger


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
    def get_user_with_profile(db: Session, user_id: int) -> User:
        """Fetches the User along with their profile relationship"""
        # return db.query(User).filter(User.id == user_id).first()
        profile = (
            db.query(User)
            .options(joinedload(User.profile))
            .filter(User.id == user_id)
            .first()
        )
        print("profile", profile.profile.profile_picture)
        return profile

    @staticmethod
    def update_user_and_profile(db: Session, user_id: int, update_data: dict):
        """Updates both User and Profile tables"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        # 1. Update User Table Fields
        if "first_name" in update_data:
            user.first_name = update_data["first_name"]
        if "last_name" in update_data:
            user.last_name = update_data["last_name"]

        # 2. Update or Create Profile Table Fields
        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        if not profile:
            profile = Profile(user_id=user_id)
            db.add(profile)

        if "gender" in update_data:
            profile.gender = update_data["gender"]
        if "pic_url" in update_data:
            profile.profile_picture = update_data["pic_url"]

        db.commit()
        db.refresh(user)
        db.refresh(profile)
        return db.query(User).options(joinedload(User.profile)).get(user_id)

    # @staticmethod
    # def update_profile_pic(
    #     db: Session, user_id: int, gender: str = None, pic_url: str = None
    # ):
    #     profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    #     # Create profile if it doesn't exist
    #     if not profile:
    #         profile = Profile(user_id=user_id, gender=None, profile_picture=pic_url )
    #         db.add(profile)
    #     else:
    #         profile.profile_picture = pic_url
    #     db.commit()
    #     db.refresh(profile)
    #     return profile

    @staticmethod
    def add_address(db: Session, user_id: int, addr_in: AddressCreate):
        db_addr = Address(**addr_in.model_dump(), user_id=user_id)
        db.add(db_addr)
        db.commit()
        db.refresh(db_addr)
        logger.info(
            "UserRepository.add_address: user_id=%s address_id=%s", user_id, db_addr.id
        )
        return db_addr
