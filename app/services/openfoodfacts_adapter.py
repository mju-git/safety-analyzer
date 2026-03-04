"""Open Food Facts API adapter for fetching product data."""
import logging
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.models import Product, Category

logger = logging.getLogger(__name__)

# Open Food Facts API base URL
OFF_API_BASE = "https://world.openfoodfacts.org/api/v0"
OFF_TIMEOUT = 10.0  # seconds


class OpenFoodFactsAdapter:
    """
    Adapter for fetching product data from Open Food Facts API.
    
    Handles:
    - Product lookup by barcode
    - Product search by name
    - Data normalization and validation
    - Source attribution
    """
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=OFF_TIMEOUT)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def fetch_by_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        """
        Fetch product data by barcode from Open Food Facts.
        
        Args:
            barcode: Product barcode (EAN-13, UPC, etc.)
            
        Returns:
            Dict with product data or None if not found
            Structure:
            {
                "name": str,
                "brand": Optional[str],
                "category": Category enum,
                "ingredients_raw": Optional[str],
                "barcode": str,
                "source": "openfoodfacts",
                "last_fetched": datetime
            }
        """
        try:
            url = f"{OFF_API_BASE}/product/{barcode}.json"
            logger.info(f"Fetching product from Open Food Facts: barcode={barcode}")
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            # Open Food Facts returns {"status": 0} if product not found
            if data.get("status") == 0:
                logger.info(f"Product not found in Open Food Facts: barcode={barcode}")
                return None
            
            product_data = data.get("product", {})
            if not product_data:
                logger.warning(f"Empty product data from Open Food Facts: barcode={barcode}")
                return None
            
            # Extract and normalize product information
            return self._normalize_product_data(product_data, barcode)
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info(f"Product not found in Open Food Facts: barcode={barcode}")
                return None
            logger.error(f"HTTP error fetching from Open Food Facts: {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error fetching from Open Food Facts: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching from Open Food Facts: {e}", exc_info=True)
            return None
    
    async def search_by_name(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for products by name in Open Food Facts.
        
        Args:
            query: Search query (product name or brand)
            limit: Maximum number of results to return
            
        Returns:
            List of product data dictionaries (same structure as fetch_by_barcode)
        """
        try:
            # Open Food Facts search endpoint
            url = f"{OFF_API_BASE}/cgi/search.pl"
            # Try simpler parameter format - remove search_simple which might cause issues
            params = {
                "search_terms": query,
                "action": "process",
                "json": 1,
                "page_size": min(limit, 20),  # API limit
                "fields": "code,product_name,product_name_en,product_name_fr,brands,brands_tags,ingredients_text,ingredients_text_en,ingredients_text_fr,categories_tags"
            }
            
            logger.info(f"Searching Open Food Facts: query={query}")
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Open Food Facts search returns products in "products" array
            products = data.get("products", [])
            
            # Log response info for debugging
            count = data.get("count", 0)
            page_size = data.get("page_size", 0)
            page = data.get("page", 0)
            logger.info(f"Open Food Facts search response: count={count}, page={page}, page_size={page_size}, products_in_response={len(products)}")
            
            # If products array is empty but count > 0, there might be an issue with the query format
            if not products:
                if count and count > 0:
                    logger.warning(f"Open Food Facts reports {count} products but returned empty array. This may indicate a query format issue for: {query}")
                else:
                    logger.info(f"No products found in Open Food Facts: query={query}")
                return []
            
            # Normalize and return product data
            normalized_products = []
            for product_data in products[:limit]:
                try:
                    # Try to get barcode, but don't require it for normalization
                    barcode = product_data.get("code") or product_data.get("id")
                    # Normalize even if no barcode (barcode will be None)
                    normalized = self._normalize_product_data(product_data, barcode)
                    if normalized:
                        normalized_products.append(normalized)
                    else:
                        logger.debug(f"Product normalization returned None for product: {product_data.get('product_name', 'unknown')}")
                except Exception as e:
                    logger.warning(f"Error normalizing product from search: {e}", exc_info=True)
                    continue
            
            logger.info(f"Found {len(normalized_products)} products in Open Food Facts: query={query}")
            return normalized_products
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error searching Open Food Facts: {e}")
            return []
        except httpx.RequestError as e:
            logger.error(f"Request error searching Open Food Facts: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching Open Food Facts: {e}", exc_info=True)
            return []
    
    def _normalize_product_data(
        self, 
        product_data: Dict[str, Any], 
        barcode: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Normalize product data from Open Food Facts format to our internal format.
        
        Treats all external data as untrusted and normalizes it.
        
        Args:
            product_data: Raw product data from Open Food Facts API
            barcode: Product barcode (may be in product_data or passed separately)
            
        Returns:
            Normalized product data dictionary or None if invalid
        """
        try:
            # Extract basic fields
            name = product_data.get("product_name") or product_data.get("product_name_en") or product_data.get("product_name_fr")
            if not name:
                logger.warning("Product missing name, skipping")
                return None
            
            # Clean and validate name
            name = name.strip()
            if not name or len(name) > 500:  # Reasonable limit
                logger.warning(f"Invalid product name: {name}")
                return None
            
            # Extract brand
            brands = product_data.get("brands") or product_data.get("brands_tags", [])
            brand = None
            if isinstance(brands, str):
                # Sometimes brands is a comma-separated string
                brand_list = [b.strip() for b in brands.split(",")]
                brand = brand_list[0] if brand_list else None
            elif isinstance(brands, list) and brands:
                brand = brands[0] if isinstance(brands[0], str) else None
            
            if brand:
                brand = brand.strip()
                if len(brand) > 200:  # Reasonable limit
                    brand = brand[:200]
            
            # Extract barcode
            extracted_barcode = barcode or product_data.get("code") or product_data.get("id")
            if extracted_barcode:
                extracted_barcode = str(extracted_barcode).strip()
            
            # Extract ingredients (treat as untrusted input)
            # Prioritize English, then fall back to other languages
            ingredients_raw = (
                product_data.get("ingredients_text_en") or 
                product_data.get("ingredients_text") or 
                product_data.get("ingredients_text_fr") or
                product_data.get("ingredients_text_de") or
                product_data.get("ingredients_text_es")
            )
            if ingredients_raw:
                # Clean and validate ingredients text
                ingredients_raw = ingredients_raw.strip()
                # Limit size to prevent abuse
                if len(ingredients_raw) > 10000:
                    logger.warning(f"Ingredients text too long, truncating: {len(ingredients_raw)} chars")
                    ingredients_raw = ingredients_raw[:10000]
            
            # Determine category (default to FOOD for Open Food Facts)
            # Open Food Facts is primarily food products
            category = Category.FOOD
            
            # Check categories_tags for more specific category
            categories = product_data.get("categories_tags", [])
            if categories:
                categories_lower = [c.lower() for c in categories if isinstance(c, str)]
                # Map to our categories if possible
                if any("cosmetic" in c for c in categories_lower):
                    category = Category.COSMETIC
                elif any("household" in c or "cleaning" in c for c in categories_lower):
                    category = Category.HOUSEHOLD
                elif any("supplement" in c or "vitamin" in c for c in categories_lower):
                    category = Category.SUPPLEMENT
            
            return {
                "name": name,
                "brand": brand,
                "category": category,
                "ingredients_raw": ingredients_raw,
                "barcode": extracted_barcode,
                "source": "openfoodfacts",
                "last_fetched": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error normalizing product data: {e}", exc_info=True)
            return None
    
    def create_or_update_product(
        self,
        db_session,
        product_data: Dict[str, Any]
    ) -> Optional[Product]:
        """
        Create or update a product in the database from Open Food Facts data.
        
        Args:
            db_session: SQLAlchemy database session
            product_data: Normalized product data dictionary
            
        Returns:
            Product model instance or None if creation failed
        """
        try:
            # Check if product exists by barcode
            product = None
            if product_data.get("barcode"):
                product = db_session.query(Product).filter(
                    Product.barcode == product_data["barcode"]
                ).first()
            
            # If not found by barcode, try to find by name and brand
            if not product and product_data.get("name") and product_data.get("brand"):
                product = db_session.query(Product).filter(
                    Product.name == product_data["name"],
                    Product.brand == product_data["brand"]
                ).first()
            
            if product:
                # Update existing product
                product.name = product_data["name"]
                product.brand = product_data.get("brand")
                product.category = product_data["category"]
                product.ingredients_raw = product_data.get("ingredients_raw")
                product.source = product_data.get("source", "openfoodfacts")
                product.last_fetched = product_data.get("last_fetched")
                if product_data.get("barcode") and not product.barcode:
                    product.barcode = product_data["barcode"]
                logger.info(f"Updated product from Open Food Facts: id={product.id}, name={product.name}")
            else:
                # Create new product
                product = Product(
                    name=product_data["name"],
                    brand=product_data.get("brand"),
                    category=product_data["category"],
                    ingredients_raw=product_data.get("ingredients_raw"),
                    barcode=product_data.get("barcode"),
                    source=product_data.get("source", "openfoodfacts"),
                    last_fetched=product_data.get("last_fetched")
                )
                db_session.add(product)
                logger.info(f"Created product from Open Food Facts: name={product.name}")
            
            db_session.commit()
            db_session.refresh(product)
            return product
            
        except Exception as e:
            logger.error(f"Error creating/updating product from Open Food Facts: {e}", exc_info=True)
            db_session.rollback()
            return None
