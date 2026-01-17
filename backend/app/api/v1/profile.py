from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User, Address
from app.schemas.user import (
    ProfileUpdate,
    ProfileResponse,
    AddressCreate,
    AddressResponse,
)
from app.services.s3_service import S3Service
from app.repositories.user_repo import UserRepository
from typing import List

router = APIRouter()


@router.get("/profile", response_model=ProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return UserRepository.get_profile(db, current_user.id)


@router.put("/profile", response_model=ProfileResponse)
def update_my_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return UserRepository.update_profile(db, current_user.id, gender=data.gender)


@router.put("/profile/picture")
async def upload_profile_pic(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Upload to S3 (folder 'profiles')
    img_url = S3Service.upload_image(image)
    UserRepository.update_profile(db, current_user.id, pic_url=img_url)
    return {"url": img_url}


# --- Address Management ---


@router.post("/address", response_model=AddressResponse)
def add_new_address(
    addr_in: AddressCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return UserRepository.add_address(db, current_user.id, addr_in)


@router.get("/addresses", response_model=List[AddressResponse])
def list_my_addresses(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return db.query(Address).filter(Address.user_id == current_user.id).all()


@router.delete("/address/{address_id}")
def delete_address(
    address_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    addr = (
        db.query(Address)
        .filter(Address.id == address_id, Address.user_id == current_user.id)
        .first()
    )
    if not addr:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Address not found")
    db.delete(addr)
    db.commit()
    return {"detail": "Address deleted"}
