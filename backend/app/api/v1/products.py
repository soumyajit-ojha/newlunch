from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_active_seller
from app.services.s3_service import S3Service
from app.models.user import User
from app.models.product import Product
from app.schemas.product import ProductResponse

router = APIRouter()


@router.post(
    "/add", response_model=ProductResponse, status_code=status.HTTP_201_CREATED
)
async def add_mobile(
    brand: str = Form(...),
    model_name: str = Form(...),
    price: float = Form(...),
    stock: int = Form(0),
    description: str = Form(None),
    ram: int = Form(...),
    rom: int = Form(...),
    network_type: str = Form(...),
    processor: str = Form(...),
    battery: int = Form(...),
    screen_size: float = Form(...),
    image: UploadFile = File(...),
    current_seller: User = Depends(get_current_active_seller),
    db: Session = Depends(get_db),
):
    # 1. Upload to S3
    image_url = S3Service.upload_image(image)

    # 2. Create Product Record
    new_product = Product(
        brand=brand,
        model_name=model_name,
        price=price,
        stock=stock,
        description=description,
        ram=ram,
        rom=rom,
        network_type=network_type,
        processor=processor,
        battery=battery,
        screen_size=screen_size,
        image_url=image_url,
        seller_id=current_seller.id,
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product
