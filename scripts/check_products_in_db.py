"""Check what products exist in database and their ingredient status."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Product

def check_products():
    """List all products and their ingredient status."""
    db = SessionLocal()
    
    print("📦 Products in Database:\n")
    print("=" * 80)
    
    products = db.query(Product).order_by(Product.name).all()
    
    if not products:
        print("❌ No products found in database")
        db.close()
        return
    
    print(f"Total products: {len(products)}\n")
    
    for product in products:
        has_ingredients = bool(product.ingredients_raw and product.ingredients_raw.strip())
        ingredients_preview = ""
        if has_ingredients:
            ingredients_preview = product.ingredients_raw[:100] + "..." if len(product.ingredients_raw) > 100 else product.ingredients_raw
        
        status = "✅ HAS INGREDIENTS" if has_ingredients else "❌ NO INGREDIENTS"
        
        print(f"ID: {product.id}")
        print(f"  Name: {product.name}")
        print(f"  Brand: {product.brand or 'N/A'}")
        print(f"  Category: {product.category.value}")
        print(f"  Status: {status}")
        if has_ingredients:
            print(f"  Ingredients: {ingredients_preview}")
        print()
    
    print("=" * 80)
    
    # Summary
    with_ingredients = sum(1 for p in products if p.ingredients_raw and p.ingredients_raw.strip())
    without_ingredients = len(products) - with_ingredients
    
    print(f"\n📊 Summary:")
    print(f"   Products with ingredients: {with_ingredients}")
    print(f"   Products without ingredients: {without_ingredients}")
    
    db.close()

if __name__ == "__main__":
    check_products()
