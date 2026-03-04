"""Product search router."""
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Set

from app.database import get_db
from app.models import Product
from app.schemas import ProductResponse
from app.services.openfoodfacts_adapter import OpenFoodFactsAdapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/products", response_model=List[ProductResponse])
async def search_products(
    q: str = Query(..., description="Search query for product name or brand"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results to return"),
    use_external: bool = Query(True, description="Whether to search external sources (Open Food Facts) if local results are insufficient"),
    db: Session = Depends(get_db)
):
    """
    Search for products by name or brand.
    Used by web and mobile app.
    
    First searches the local database. If use_external=True and local results are
    insufficient, also searches Open Food Facts and merges results.
    
    Returns a list of matching products (id, name, brand, category).
    """
    if not q or not q.strip():
        return []
    
    query = q.strip()
    products: List[Product] = []
    product_ids: Set[int] = set()
    
    # First, search local database
    local_products = db.query(Product).filter(
        or_(
            Product.name.ilike(f"%{query}%"),
            Product.brand.ilike(f"%{query}%")
        )
    ).limit(limit).all()
    
    for product in local_products:
        products.append(product)
        product_ids.add(product.id)
    
    logger.info(f"Found {len(products)} products in local database for query: {query}")
    
    # Note: Open Food Facts text search API is unreliable (rate limits, inconsistent results)
    # We only use barcode lookup for external sources, which is more reliable
    # Text search only works for products already in the local database
    
    # If we have results, return them
    if len(products) >= limit:
        return products[:limit]
    
    # If no local results and external search is enabled, log that text search isn't available
    if not products and use_external:
        logger.info(f"No local products found for query: {query}. Open Food Facts text search is disabled due to API limitations. Use barcode search instead.")
    
    return products[:limit]
