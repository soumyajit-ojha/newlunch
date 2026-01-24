from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.product import Product
from app.utils.log_config import get_logger
from typing import List, Optional

logger = get_logger(__name__)


class ProductRepository:
    @staticmethod
    def search_products(
        db: Session,
        brand: Optional[List[str]] = None,
        ram: Optional[List[int]] = None,
        network_type: Optional[List[str]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        search_query: Optional[str] = None,
    ):
        logger.info(
            "ProductRepository.search_products: brand=%s ram=%s network=%s min_price=%s max_price=%s query=%s",
            brand,
            ram,
            network_type,
            min_price,
            max_price,
            search_query,
        )
        query = db.query(Product).filter(Product.is_active == True)

        if brand:
            query = query.filter(Product.brand.in_(brand))
        if ram:
            query = query.filter(Product.ram.in_(ram))
        if network_type:
            query = query.filter(Product.network_type.in_(network_type))
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)

        # Simple Search on Model Name
        if search_query:
            query = query.filter(Product.model_name.ilike(f"%{search_query}%"))

        results = query.order_by(Product.created_at.desc()).all()
        logger.info(
            "ProductRepository.search_products: found %d products", len(results)
        )
        return results

    @staticmethod
    def get_filter_metadata(db: Session):
        """Returns unique values for sidebar filters"""
        logger.info("ProductRepository.get_filter_metadata: fetching filter options")
        brands = db.query(Product.brand).distinct().all()
        rams = db.query(Product.ram).distinct().all()
        networks = db.query(Product.network_type).distinct().all()
        max_price = db.query(func.max(Product.price)).scalar()

        metadata = {
            "brands": [b[0] for b in brands],
            "ram_options": [r[0] for r in rams],
            "network_types": [n[0] for n in networks],
            "max_price_limit": max_price or 100000,
        }
        logger.info(
            "ProductRepository.get_filter_metadata: %d brands, %d ram_options, %d networks, max_price=%s",
            len(metadata["brands"]),
            len(metadata["ram_options"]),
            len(metadata["network_types"]),
            max_price,
        )
        return metadata
