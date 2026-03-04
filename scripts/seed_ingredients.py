"""Script to seed the database with example ingredients and safety profiles."""
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import (
    Ingredient, IngredientSafety,
    EvidenceStrength, ExposureRoute, RiskLevel, PopulationRisk
)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)


def seed_ingredients(db: Session):
    """Seed the database with example ingredients and safety profiles."""
    
    # Define ingredients with their safety profiles
    ingredients_data = [
        {
            "name": "Water",
            "inci_name": "Aqua",
            "cas_number": "7732-18-5",
            "category": "solvent",
            "evidence_strength": EvidenceStrength.HIGH,
            "notes": "Universal solvent, safe for all uses",
            "safety_profiles": [
                {
                    "exposure_route": ExposureRoute.INGESTION,
                    "safe_limit": None,
                    "unit": None,
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Essential for life, no known safety concerns",
                    "source": "EFSA"
                },
                {
                    "exposure_route": ExposureRoute.SKIN,
                    "safe_limit": None,
                    "unit": None,
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Safe for topical use",
                    "source": "SCCS"
                }
            ]
        },
        {
            "name": "Sodium Chloride",
            "inci_name": None,
            "cas_number": "7647-14-5",
            "category": "preservative",
            "evidence_strength": EvidenceStrength.HIGH,
            "notes": "Common salt, used as preservative and flavor enhancer",
            "safety_profiles": [
                {
                    "exposure_route": ExposureRoute.INGESTION,
                    "safe_limit": 5.0,
                    "unit": "g/day",
                    "risk_level": RiskLevel.MODERATE,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Excessive intake may increase blood pressure",
                    "source": "EFSA"
                }
            ]
        },
        {
            "name": "Citric Acid",
            "inci_name": None,
            "cas_number": "77-92-9",
            "category": "preservative",
            "evidence_strength": EvidenceStrength.HIGH,
            "notes": "Natural preservative and flavoring agent",
            "safety_profiles": [
                {
                    "exposure_route": ExposureRoute.INGESTION,
                    "safe_limit": None,
                    "unit": None,
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Generally recognized as safe (GRAS)",
                    "source": "EFSA"
                }
            ]
        },
        {
            "name": "Sodium Hydroxide",
            "inci_name": None,
            "cas_number": "1310-73-2",
            "category": "pH adjuster",
            "evidence_strength": EvidenceStrength.HIGH,
            "notes": "Strong base, used for pH adjustment",
            "safety_profiles": [
                {
                    "exposure_route": ExposureRoute.SKIN,
                    "safe_limit": 0.5,
                    "unit": "%",
                    "risk_level": RiskLevel.HIGH,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Can cause skin irritation and burns at high concentrations",
                    "source": "SCCS"
                },
                {
                    "exposure_route": ExposureRoute.INGESTION,
                    "safe_limit": 0.1,
                    "unit": "%",
                    "risk_level": RiskLevel.HIGH,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Corrosive, can cause severe burns",
                    "source": "EFSA"
                }
            ]
        },
        {
            "name": "Titanium Dioxide",
            "inci_name": "Titanium Dioxide",
            "cas_number": "13463-67-7",
            "category": "colorant",
            "evidence_strength": EvidenceStrength.MEDIUM,
            "notes": "White pigment used in cosmetics and food",
            "safety_profiles": [
                {
                    "exposure_route": ExposureRoute.SKIN,
                    "safe_limit": 25.0,
                    "unit": "%",
                    "risk_level": RiskLevel.MODERATE,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Safe for topical use, avoid inhalation of nanoparticles",
                    "source": "SCCS"
                },
                {
                    "exposure_route": ExposureRoute.INGESTION,
                    "safe_limit": None,
                    "unit": None,
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Approved food additive, generally safe",
                    "source": "EFSA"
                }
            ]
        },
        {
            "name": "BHT",
            "inci_name": None,
            "cas_number": "128-37-0",
            "category": "antioxidant",
            "evidence_strength": EvidenceStrength.MEDIUM,
            "notes": "Butylated Hydroxytoluene, synthetic antioxidant",
            "safety_profiles": [
                {
                    "exposure_route": ExposureRoute.INGESTION,
                    "safe_limit": 0.25,
                    "unit": "mg/kg body weight/day",
                    "risk_level": RiskLevel.MODERATE,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Acceptable daily intake established, some concerns about endocrine effects",
                    "source": "EFSA"
                }
            ]
        },
        {
            "name": "Propylene Glycol",
            "inci_name": "Propylene Glycol",
            "cas_number": "57-55-6",
            "category": "humectant",
            "evidence_strength": EvidenceStrength.HIGH,
            "notes": "Common humectant in cosmetics and food",
            "safety_profiles": [
                {
                    "exposure_route": ExposureRoute.SKIN,
                    "safe_limit": 50.0,
                    "unit": "%",
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.SENSITIVE_SKIN,
                    "summary": "May cause irritation in sensitive individuals at high concentrations",
                    "source": "SCCS"
                },
                {
                    "exposure_route": ExposureRoute.INGESTION,
                    "safe_limit": 25.0,
                    "unit": "mg/kg body weight/day",
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Generally recognized as safe for food use",
                    "source": "EFSA"
                }
            ]
        },
        {
            "name": "Parabens",
            "inci_name": None,
            "cas_number": None,
            "category": "preservative",
            "evidence_strength": EvidenceStrength.MEDIUM,
            "notes": "Class of preservatives, includes methylparaben, propylparaben",
            "safety_profiles": [
                {
                    "exposure_route": ExposureRoute.SKIN,
                    "safe_limit": 0.8,
                    "unit": "%",
                    "risk_level": RiskLevel.MODERATE,
                    "population_risk": PopulationRisk.PREGNANCY,
                    "summary": "Some concerns about endocrine disruption, especially during pregnancy",
                    "source": "SCCS"
                }
            ]
        },
        {
            "name": "Vitamin C",
            "inci_name": "Ascorbic Acid",
            "cas_number": "50-81-7",
            "category": "antioxidant",
            "evidence_strength": EvidenceStrength.HIGH,
            "notes": "Essential vitamin and antioxidant",
            "safety_profiles": [
                {
                    "exposure_route": ExposureRoute.INGESTION,
                    "safe_limit": 2000.0,
                    "unit": "mg/day",
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Essential nutrient, safe at recommended levels",
                    "source": "EFSA"
                },
                {
                    "exposure_route": ExposureRoute.SKIN,
                    "safe_limit": 20.0,
                    "unit": "%",
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.SENSITIVE_SKIN,
                    "summary": "May cause mild irritation in sensitive skin at high concentrations",
                    "source": "SCCS"
                }
            ]
        },
        {
            "name": "Sodium Lauryl Sulfate",
            "inci_name": "Sodium Lauryl Sulfate",
            "cas_number": "151-21-3",
            "category": "surfactant",
            "evidence_strength": EvidenceStrength.HIGH,
            "notes": "Common surfactant in personal care products",
            "safety_profiles": [
                {
                    "exposure_route": ExposureRoute.SKIN,
                    "safe_limit": 1.0,
                    "unit": "%",
                    "risk_level": RiskLevel.MODERATE,
                    "population_risk": PopulationRisk.SENSITIVE_SKIN,
                    "summary": "Can cause skin irritation and dryness, especially in sensitive individuals",
                    "source": "SCCS"
                },
                {
                    "exposure_route": ExposureRoute.INGESTION,
                    "safe_limit": 0.5,
                    "unit": "%",
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Low oral toxicity, used in small amounts in food",
                    "source": "EFSA"
                }
            ]
        }
    ]
    
    created_count = 0
    skipped_count = 0
    
    for ing_data in ingredients_data:
        # Check if ingredient already exists
        existing = db.query(Ingredient).filter(
            Ingredient.name == ing_data["name"]
        ).first()
        
        if existing:
            print(f"⏭️  Skipping {ing_data['name']} (already exists)")
            skipped_count += 1
            continue
        
        # Create ingredient
        ingredient = Ingredient(
            name=ing_data["name"],
            inci_name=ing_data.get("inci_name"),
            cas_number=ing_data.get("cas_number"),
            category=ing_data.get("category"),
            evidence_strength=ing_data.get("evidence_strength"),
            notes=ing_data.get("notes")
        )
        
        db.add(ingredient)
        db.flush()  # Flush to get ingredient.id
        
        # Create safety profiles
        for profile_data in ing_data.get("safety_profiles", []):
            safety_profile = IngredientSafety(
                ingredient_id=ingredient.id,
                exposure_route=profile_data["exposure_route"],
                safe_limit=profile_data.get("safe_limit"),
                unit=profile_data.get("unit"),
                risk_level=profile_data["risk_level"],
                population_risk=profile_data["population_risk"],
                summary=profile_data.get("summary"),
                source=profile_data.get("source")
            )
            db.add(safety_profile)
        
        created_count += 1
        print(f"✅ Created {ing_data['name']} with {len(ing_data.get('safety_profiles', []))} safety profile(s)")
    
    # Commit all changes
    db.commit()
    
    print(f"\n📊 Summary:")
    print(f"   Created: {created_count} ingredients")
    print(f"   Skipped: {skipped_count} ingredients (already exist)")
    print(f"   Total: {created_count + skipped_count} ingredients processed")


if __name__ == "__main__":
    print("🌱 Seeding database with example ingredients and safety profiles...\n")
    
    db = SessionLocal()
    try:
        seed_ingredients(db)
        print("\n✨ Seeding completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error seeding database: {e}")
        raise
    finally:
        db.close()
