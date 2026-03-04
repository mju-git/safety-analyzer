"""Product resolver service for looking up products in the database."""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models import Product


class ProductResolver:
    """Service for resolving products by name and brand."""
    
    @staticmethod
    def lookup(
        db: Session,
        name: str,
        brand: Optional[str] = None
    ) -> Optional[Product]:
        """
        Look up a product by name and optional brand in the database.
        
        Performs case-insensitive search on product name and brand fields.
        If brand is provided, both name and brand must match.
        
        Args:
            db: Database session
            name: Product name to search for (required)
            brand: Optional brand name to match
        
        Returns:
            Product if found, None otherwise
        """
        query = db.query(Product)
        
        # Build search conditions for name (case-insensitive)
        name_conditions = [
            Product.name.ilike(name),  # Exact match
            Product.name.ilike(f"%{name}%")  # Partial match
        ]
        
        if brand:
            # If brand is provided, require both name and brand to match
            brand_conditions = [
                Product.brand.ilike(brand),  # Exact match
                Product.brand.ilike(f"%{brand}%")  # Partial match
            ]
            # Combine: (name exact OR name partial) AND (brand exact OR brand partial)
            query = query.filter(
                and_(
                    or_(*name_conditions),
                    or_(*brand_conditions)
                )
            )
        else:
            # If no brand, just match name
            query = query.filter(or_(*name_conditions))
        
        # Order by name to prioritize exact matches
        query = query.order_by(Product.name)
        
        # Return first match or None
        return query.first()
