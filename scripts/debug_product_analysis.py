"""Debug script to test product analysis for specific products."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Product
from app.routers.analysis import _analyze_product
import traceback

def debug_product_analysis(product_name: str):
    """Debug analysis for a specific product."""
    db = SessionLocal()
    
    print(f"🔍 Debugging analysis for: {product_name}\n")
    print("=" * 60)
    
    # Find product
    product = db.query(Product).filter(
        Product.name.ilike(f"%{product_name}%")
    ).first()
    
    if not product:
        print(f"❌ Product '{product_name}' not found in database")
        db.close()
        return
    
    print(f"✅ Found product:")
    print(f"   ID: {product.id}")
    print(f"   Name: {product.name}")
    print(f"   Brand: {product.brand}")
    print(f"   Category: {product.category}")
    print(f"   Has ingredients_raw: {bool(product.ingredients_raw)}")
    if product.ingredients_raw:
        print(f"   Ingredients length: {len(product.ingredients_raw)}")
        print(f"   Ingredients preview: {product.ingredients_raw[:200]}...")
    print()
    
    # Try to analyze
    print("🧪 Attempting analysis...\n")
    try:
        analysis = _analyze_product(
            db=db,
            product=product,
            user_profile=None
        )
        
        print("✅ Analysis completed successfully!\n")
        print("📊 Analysis Result:")
        print(f"   Product ID: {analysis.get('product_id')}")
        print(f"   Safety Score: {analysis.get('safety_score')}")
        print(f"   Has explanation: {bool(analysis.get('explanation'))}")
        
        explanation = analysis.get('explanation', {})
        flagged = explanation.get('flagged_ingredients', [])
        beneficial = explanation.get('beneficial_ingredients', [])
        
        print(f"   Flagged ingredients: {len(flagged)}")
        print(f"   Beneficial ingredients: {len(beneficial)}")
        print(f"   Recommendation: {explanation.get('recommendation', 'N/A')[:100]}...")
        
        if flagged:
            print("\n📋 Flagged Ingredients:")
            for i, ing in enumerate(flagged[:5], 1):  # Show first 5
                print(f"   {i}. {ing.get('name', 'Unknown')}")
                print(f"      Risk: {ing.get('risk_level', 'N/A')}")
                print(f"      Confidence: {ing.get('confidence', 'N/A')}")
                print(f"      Has notes: {bool(ing.get('notes'))}")
                print(f"      Has sources: {bool(ing.get('sources'))}")
        
    except Exception as e:
        print(f"❌ ERROR during analysis:")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        print("\n📋 Full traceback:")
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        product_name = sys.argv[1]
    else:
        product_name = input("Enter product name to debug (e.g., 'cola', 'colgate'): ").strip()
    
    if product_name:
        debug_product_analysis(product_name)
    else:
        print("❌ No product name provided")
