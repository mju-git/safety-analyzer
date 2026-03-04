"""Barcode scanning router."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import Product
from app.schemas import ProductResponse
from app.services.openfoodfacts_adapter import OpenFoodFactsAdapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scan", tags=["barcode"])


class BarcodeRequest(BaseModel):
    """Request model for barcode scan."""
    barcode: str


@router.post("/barcode", response_model=ProductResponse)
async def scan_barcode(
    request: BarcodeRequest,
    db: Session = Depends(get_db)
):
    """
    Search for product by barcode.
    Used by mobile app only.
    
    First checks the local database. If not found, fetches from Open Food Facts
    and stores the product locally for future use.
    
    Returns the product if found, otherwise raises 404.
    """
    # First, check local database
    product = db.query(Product).filter(Product.barcode == request.barcode).first()
    
    if product:
        logger.info(f"Product found in local database: barcode={request.barcode}")
        return product
    
    # Not found locally, try Open Food Facts
    logger.info(f"Product not found locally, fetching from Open Food Facts: barcode={request.barcode}")
    adapter = OpenFoodFactsAdapter()
    
    try:
        product_data = await adapter.fetch_by_barcode(request.barcode)
        
        if not product_data:
            raise HTTPException(
                status_code=404, 
                detail=f"Product not found for barcode {request.barcode} in local database or Open Food Facts"
            )
        
        # Create or update product in database
        product = adapter.create_or_update_product(db, product_data)
        
        if not product:
            raise HTTPException(
                status_code=500,
                detail="Failed to save product from Open Food Facts to database"
            )
        
        logger.info(f"Product fetched from Open Food Facts and saved: id={product.id}, name={product.name}")
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product from Open Food Facts: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching product from external source: {str(e)}"
        )
    finally:
        await adapter.close()
