from fastapi import APIRouter, Depends, UploadFile, File, Form, status, Query, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.routers.deps import get_current_active_seller
from app.services.s3_service import S3Service
from app.models.user import User
from app.models.product import Product
from app.schemas.product import ProductResponse
from app.repositories.product_repo import ProductRepository
from app.schemas.product import FilterOptionsResponse, ProductResponse
from app.utils.log_config import logger
from typing import List, Optional

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
    logger.info("Adding product: brand=%s model=%s seller_id=%s", brand, model_name, current_seller.id)
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
    logger.info("Product added successfully: id=%s", new_product.id)
    return new_product


@router.get("/search", response_model=List[ProductResponse])
def search_mobiles(
    brand: Optional[List[str]] = Query(None),
    ram: Optional[List[int]] = Query(None),
    network: Optional[List[str]] = Query(None),
    min_p: Optional[float] = None,
    max_p: Optional[float] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """The main endpoint for the Home Page and Search Bar"""
    logger.info("Product search: brand=%s ram=%s network=%s min_p=%s max_p=%s q=%s", brand, ram, network, min_p, max_p, q)
    results = ProductRepository.search_products(db, brand, ram, network, min_p, max_p, q)
    logger.info("Product search returned %d results", len(results))
    return results


@router.get("/filter-options", response_model=FilterOptionsResponse)
def get_filters(db: Session = Depends(get_db)):
    """Used by React to build the dynamic sidebar"""
    logger.info("Fetching filter options")
    return ProductRepository.get_filter_metadata(db)


@router.get("/my-inventory", response_model=List[ProductResponse])
def get_seller_inventory(
    current_seller: User = Depends(get_current_active_seller),
    db: Session = Depends(get_db),
):
    """Returns only products belonging to the logged-in seller"""
    logger.info("Fetching seller inventory: seller_id=%s", current_seller.id)
    items = db.query(Product).filter(Product.seller_id == current_seller.id).all()
    logger.info("Seller inventory: %d products", len(items))
    return items


@router.get("/{product_id}", response_model=ProductResponse)
def get_product_details(product_id: int, db: Session = Depends(get_db)):
    """Retrieve a single mobile's details"""

    logger.info("Fetching product details: product_id=%s", product_id)
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_active == True)
        .first()
    )
    if not product:
        logger.warning("Product not found: product_id=%s", product_id)
        raise HTTPException(status_code=404, detail="Product not found")
    return product
