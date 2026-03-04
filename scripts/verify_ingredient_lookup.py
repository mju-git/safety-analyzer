"""Script to verify ingredient lookup functionality."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.routers.analysis import _lookup_ingredient_by_name_or_alias
from app.models import Ingredient

def verify_ingredient_lookup():
    """Test ingredient lookup by name and aliases."""
    db = SessionLocal()
    
    print("🔍 Testing Ingredient Lookup\n")
    
    # Test cases
    test_cases = [
        "Sodium Lauryl Sulfate",  # Direct name
        "SLS",  # Alias
        "SDS",  # Alias
        "Caffeine",  # Direct name
        "Parabens",  # Direct name
        "Methylparaben",  # Alias
        "Phosphoric Acid",  # Direct name
        "Fragrance",  # Direct name
        "Parfum",  # INCI name
        "Unknown Ingredient XYZ123"  # Should not be found
    ]
    
    results = []
    for test_name in test_cases:
        ingredient = _lookup_ingredient_by_name_or_alias(db, test_name)
        if ingredient:
            print(f"✅ Found: '{test_name}' → {ingredient.name}")
            print(f"   - INCI: {ingredient.inci_name}")
            print(f"   - Confidence: {ingredient.confidence.value if ingredient.confidence else 'None'}")
            print(f"   - Sources: {ingredient.sources}")
            print(f"   - Has notes: {bool(ingredient.notes)}")
            print()
            results.append(True)
        else:
            print(f"❌ Not found: '{test_name}'")
            print()
            results.append(False)
    
    # Summary
    found_count = sum(results)
    total_count = len(results)
    print(f"\n📊 Summary: {found_count}/{total_count} ingredients found")
    
    if found_count >= 5:  # At least 5 should be found if seed script ran
        print("✅ Ingredient lookup is working correctly!")
    else:
        print("⚠️  Warning: Many ingredients not found. Did you run the seed script?")
        print("   Run: python scripts/seed_ingredient_knowledge_base.py")
    
    db.close()

if __name__ == "__main__":
    verify_ingredient_lookup()
