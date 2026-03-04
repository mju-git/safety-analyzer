"""Script to seed the database with example products for testing."""
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import Product, Category

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)


def seed_products(db: Session):
    """Seed the database with example products."""
    
    products_data = [
        {
            "name": "COSRX Full Fit Propolis Synergy Toner",
            "brand": "COSRX",
            "category": Category.COSMETIC,
            "ingredients_raw": "Propolis Extract, Butylene Glycol, Glycerin, Sodium Hyaluronate, 1,2-Hexanediol",
            "source": "manual"
        },
        {
            "name": "CeraVe Moisturizing Cream",
            "brand": "CeraVe",
            "category": Category.COSMETIC,
            "ingredients_raw": "Purified Water, Glycerin, Cetearyl Alcohol, Caprylic/Capric Triglyceride, Ceramide NP, Ceramide AP, Ceramide EOP, Cholesterol, Sodium Hyaluronate",
            "source": "manual"
        },
        {
            "name": "Coca-Cola Original Taste",
            "brand": "Coca-Cola",
            "category": Category.FOOD,
            "ingredients_raw": "Carbonated Water, Sugar, Caramel Color, Phosphoric Acid, Natural Flavors, Caffeine",
            "source": "manual"
        },
        {
            "name": "Colgate Total Toothpaste",
            "brand": "Colgate",
            "category": Category.HOUSEHOLD,
            "ingredients_raw": "Sodium Fluoride, Water, Sorbitol, Hydrated Silica, Glycerin, PEG-12, Sodium Lauryl Sulfate, Flavor",
            "source": "manual"
        }
    ]
    
    created_count = 0
    skipped_count = 0
    
    for product_data in products_data:
        # Check if product already exists (by name and brand)
        existing = db.query(Product).filter(
            Product.name == product_data["name"],
            Product.brand == product_data.get("brand")
        ).first()
        
        if existing:
            print(f"⏭️  Skipping {product_data['name']} (already exists)")
            skipped_count += 1
            continue
        
        # Create product
        product = Product(
            name=product_data["name"],
            brand=product_data.get("brand"),
            category=product_data["category"],
            ingredients_raw=product_data.get("ingredients_raw"),
            source=product_data.get("source", "manual")
        )
        
        db.add(product)
        created_count += 1
        print(f"✅ Created {product_data['name']}")
    
    # Commit all changes
    db.commit()
    
    print(f"\n📊 Summary:")
    print(f"   Created: {created_count} products")
    print(f"   Skipped: {skipped_count} products (already exist)")
    print(f"   Total: {created_count + skipped_count} products processed")


if __name__ == "__main__":
    print("🌱 Seeding database with example products...\n")
    
    db = SessionLocal()
    try:
        seed_products(db)
        print("\n✨ Seeding completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()
