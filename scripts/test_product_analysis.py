"""Script to test product analysis and verify output structure."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Product
from app.routers.analysis import _analyze_product
from app.routers.analysis import UserProfile

def test_product_analysis():
    """Test product analysis and verify all required fields are present."""
    db = SessionLocal()
    
    print("🧪 Testing Product Analysis\n")
    
    # Find a product with ingredients
    product = db.query(Product).filter(
        Product.ingredients_raw.isnot(None),
        Product.ingredients_raw != ''
    ).first()
    
    if not product:
        print("❌ No products with ingredients found in database!")
        print("   Please add ingredients_raw to at least one product.")
        db.close()
        return
    
    print(f"📦 Testing with product: {product.name}")
    if product.brand:
        print(f"   Brand: {product.brand}")
    print(f"   Ingredients: {product.ingredients_raw[:100]}...")
    print()
    
    # Run analysis
    try:
        analysis = _analyze_product(
            db=db,
            product=product,
            user_profile=None
        )
        
        print("✅ Analysis completed successfully!\n")
        print("=" * 60)
        print("ANALYSIS OUTPUT STRUCTURE")
        print("=" * 60)
        print(json.dumps(analysis, indent=2, default=str))
        print("=" * 60)
        print()
        
        # Verify required fields
        print("🔍 Verifying Required Fields:\n")
        
        checks = {
            "product_id": analysis.get("product_id") is not None,
            "safety_score": analysis.get("safety_score") is not None,
            "explanation": analysis.get("explanation") is not None,
            "computed_at": analysis.get("computed_at") is not None,
        }
        
        explanation = analysis.get("explanation", {})
        exp_checks = {
            "flagged_ingredients": explanation.get("flagged_ingredients") is not None,
            "beneficial_ingredients": explanation.get("beneficial_ingredients") is not None,
            "recommendation": explanation.get("recommendation") is not None,
        }
        
        all_passed = True
        for field, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} {field}: {passed}")
            if not passed:
                all_passed = False
        
        for field, passed in exp_checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} explanation.{field}: {passed}")
            if not passed:
                all_passed = False
        
        # Check flagged ingredients structure
        flagged = explanation.get("flagged_ingredients", [])
        if flagged:
            print(f"\n📋 Checking {len(flagged)} flagged ingredient(s):\n")
            for i, ing in enumerate(flagged, 1):
                print(f"  Ingredient {i}: {ing.get('name', 'Unknown')}")
                ing_checks = {
                    "risk_level": ing.get("risk_level") is not None,
                    "confidence": ing.get("confidence") is not None,
                    "notes": ing.get("notes") is not None,
                    "sources": ing.get("sources") is not None or ing.get("evidence_source") is not None,
                }
                
                for field, passed in ing_checks.items():
                    status = "✅" if passed else "❌"
                    value = ing.get(field, "MISSING")
                    print(f"    {status} {field}: {value}")
                    if not passed:
                        all_passed = False
                
                # Special check for unknown ingredients
                if ing.get("is_unknown") or ing.get("confidence") == "unknown":
                    risk = ing.get("risk_level")
                    if risk == "unknown":
                        print(f"    ✅ Unknown ingredient correctly shows risk_level='unknown'")
                    else:
                        print(f"    ❌ Unknown ingredient has risk_level='{risk}' (should be 'unknown')")
                        all_passed = False
                print()
        else:
            print("\n📋 No flagged ingredients (this is OK if product has no risky ingredients)")
        
        if all_passed:
            print("\n✅ All required fields are present and correct!")
        else:
            print("\n❌ Some required fields are missing or incorrect!")
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    
    db.close()

if __name__ == "__main__":
    test_product_analysis()
