from fastapi import APIRouter, Depends, UploadFile, File, status, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.routers.deps import get_current_user
from app.models.user import User, Address
from app.schemas.user import (
    ProfileUpdate,
    ProfileResponse,
    AddressCreate,
    AddressResponse,
)
from app.services.s3_service import S3Service
from app.repositories.user_repo import UserRepository
from app.utils.log_config import logger
from typing import List

router = APIRouter()


@router.get("/profile", response_model=ProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    logger.info("Get profile: user_id=%s", current_user.id)
    profile = UserRepository.get_user_with_profile(db, current_user.id)
    if not profile:
        from app.models.user import Profile

        logger.info("Creating default profile for user_id=%s", current_user.id)
        profile = Profile(user_id=current_user.id, gender=None, profile_picture=None)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


# @router.put("/profile", response_model=ProfileResponse)
# def update_my_profile(
#     data: ProfileUpdate,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db),
# ):
#     logger.info("Update profile: user_id=%s", current_user.id)
#     try:
#         return UserRepository.update_profile(db, current_user.id, gender=data.gender)
#     except Exception as e:
#         print("Error", str(e))
#         return None


@router.put("/profile", response_model=ProfileResponse)
def update_my_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        "Update profile: user_id=%s data=%s",
        current_user.id,
        data.model_dump(exclude_unset=True),
    )
    try:
        updated_user = UserRepository.update_user_and_profile(
            db, user_id=current_user.id, update_data=data.model_dump(exclude_unset=True)
        )
        if not updated_user:
            logger.error(
                "Profile update failed: user not found user_id=%s", current_user.id
            )
            raise HTTPException(status_code=404, detail="User not found")
        logger.info("Profile updated successfully: user_id=%s", current_user.id)
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Profile update error: user_id=%s error=%s", current_user.id, str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to update profile")


@router.put("/profile/picture")
async def upload_profile_pic(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info("Upload profile picture: user_id=%s", current_user.id)
    img_url = S3Service.upload_image(image, max_file_size=5)
    UserRepository.update_profile(db, current_user.id, pic_url=img_url)
    logger.info("Profile picture updated: user_id=%s", current_user.id)
    return {"url": img_url}


# --- Address Management ---


@router.post("/address", response_model=AddressResponse)
def add_new_address(
    addr_in: AddressCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info("Add address: user_id=%s", current_user.id)
    return UserRepository.add_address(db, current_user.id, addr_in)


@router.get("/addresses", response_model=List[AddressResponse])
def list_my_addresses(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    logger.info("List addresses: user_id=%s", current_user.id)
    return db.query(Address).filter(Address.user_id == current_user.id).all()


@router.delete("/address/{address_id}")
def delete_address(
    address_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info("Delete address: user_id=%s address_id=%s", current_user.id, address_id)
    addr = (
        db.query(Address)
        .filter(Address.id == address_id, Address.user_id == current_user.id)
        .first()
    )
    if not addr:
        logger.warning(
            "Address not found: address_id=%s user_id=%s", address_id, current_user.id
        )
        raise HTTPException(status_code=404, detail="Address not found")
    db.delete(addr)
    db.commit()
    logger.info("Address deleted: address_id=%s", address_id)
    return {"detail": "Address deleted"}
