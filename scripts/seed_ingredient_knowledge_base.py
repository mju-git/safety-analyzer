"""Script to seed the ingredient knowledge base with curated ingredients."""
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import (
    Ingredient, IngredientSafety,
    EvidenceStrength, ExposureRoute, RiskLevel, PopulationRisk, ConfidenceLevel, Category
)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)


def seed_ingredient_knowledge_base(db: Session):
    """Seed the ingredient knowledge base with curated ingredients."""
    
    # Define curated ingredients with comprehensive safety data
    ingredients_data = [
        {
            "name": "Sodium Lauryl Sulfate",
            "inci_name": "Sodium Lauryl Sulfate",
            "cas_number": "151-21-3",
            "aliases": ["SLS", "Sodium Dodecyl Sulfate", "SDS", "Sodium Laurylsulfate"],
            "category": "cosmetic",
            "evidence_strength": EvidenceStrength.HIGH,
            "confidence": ConfidenceLevel.HIGH,
            "notes": (
                "Surfactant commonly used in personal care products. "
                "Can cause skin irritation and dryness, especially in sensitive individuals. "
                "Safe at concentrations below 1% for most users. "
                "May cause eye irritation. Avoid in products for sensitive skin or children."
            ),
            "sources": ["SCCS", "CIR", "FDA"],
            "safety_profiles": [
                {
                    "exposure_route": ExposureRoute.SKIN,
                    "safe_limit": 1.0,
                    "unit": "%",
                    "risk_level": RiskLevel.MODERATE,
                    "population_risk": PopulationRisk.SENSITIVE_SKIN,
                    "summary": "Can cause skin irritation and dryness, especially in sensitive individuals at concentrations above 1%",
                    "source": "SCCS",
                    "reference_id": "SCCS/1234/12",  # Placeholder - replace with actual reference
                    "document_name": "Opinion on Sodium Lauryl Sulfate",  # Placeholder
                    "evidence_strength": EvidenceStrength.HIGH
                },
                {
                    "exposure_route": ExposureRoute.SKIN,
                    "safe_limit": 1.0,
                    "unit": "%",
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Generally safe for most users at low concentrations",
                    "source": "CIR",
                    "reference_id": "CIR-2020-001",  # Placeholder - replace with actual reference
                    "document_name": "Final Report on Sodium Lauryl Sulfate Safety Assessment",  # Placeholder
                    "evidence_strength": EvidenceStrength.HIGH
                },
                {
                    "exposure_route": ExposureRoute.INGESTION,
                    "safe_limit": 0.5,
                    "unit": "%",
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Low oral toxicity, used in small amounts in food products",
                    "source": "EFSA",
                    "reference_id": "EFSA-Q-2020-00123",  # Placeholder - replace with actual reference
                    "document_name": "Scientific Opinion on Sodium Lauryl Sulfate as Food Additive",  # Placeholder
                    "evidence_strength": EvidenceStrength.HIGH
                }
            ]
        },
        {
            "name": "Fragrance",
            "inci_name": "Parfum",
            "cas_number": None,
            "aliases": ["Parfum", "Aroma", "Fragrance Blend", "Perfume", "Scent"],
            "category": "cosmetic",
            "evidence_strength": EvidenceStrength.MEDIUM,
            "confidence": ConfidenceLevel.MEDIUM,
            "notes": (
                "Complex mixture of fragrance compounds. "
                "May contain allergens and sensitizers. "
                "EU regulations require disclosure of 26 known allergens if present above 0.001% in leave-on products. "
                "Can cause contact dermatitis, especially in sensitive individuals. "
                "Formulation-dependent - exact composition varies by product."
            ),
            "sources": ["SCCS", "EU Cosmetics Regulation", "IFRA"],
            "safety_profiles": [
                {
                    "exposure_route": ExposureRoute.SKIN,
                    "safe_limit": None,
                    "unit": None,
                    "risk_level": RiskLevel.MODERATE,
                    "population_risk": PopulationRisk.SENSITIVE_SKIN,
                    "summary": "May cause contact dermatitis and allergic reactions, especially in sensitive individuals. Composition varies by product.",
                    "source": "SCCS"
                },
                {
                    "exposure_route": ExposureRoute.INGESTION,
                    "safe_limit": None,
                    "unit": None,
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Generally safe in food products when used as approved food flavorings",
                    "source": "EFSA"
                },
                {
                    "exposure_route": ExposureRoute.INHALATION,
                    "safe_limit": None,
                    "unit": None,
                    "risk_level": RiskLevel.MODERATE,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "May cause respiratory irritation in some individuals",
                    "source": "IFRA"
                }
            ]
        },
        {
            "name": "Parabens",
            "inci_name": None,
            "cas_number": None,
            "aliases": [
                "Methylparaben", "Propylparaben", "Butylparaben", "Ethylparaben",
                "Paraben", "Parabens", "p-Hydroxybenzoic acid esters"
            ],
            "category": "cosmetic",
            "evidence_strength": EvidenceStrength.MEDIUM,
            "confidence": ConfidenceLevel.MEDIUM,
            "notes": (
                "Class of preservatives including methylparaben, propylparaben, butylparaben, ethylparaben. "
                "Effective antimicrobial preservatives. "
                "Some concerns about potential endocrine disruption, especially during pregnancy. "
                "EU and FDA consider them safe at current usage levels. "
                "Maximum allowed concentration: 0.8% for single paraben, 0.4% for propylparaben and butylparaben."
            ),
            "sources": ["SCCS", "FDA", "EU Cosmetics Regulation"],
            "safety_profiles": [
                {
                    "exposure_route": ExposureRoute.SKIN,
                    "safe_limit": 0.8,
                    "unit": "%",
                    "risk_level": RiskLevel.MODERATE,
                    "population_risk": PopulationRisk.PREGNANCY,
                    "summary": "Some concerns about endocrine disruption, especially during pregnancy. Considered safe at regulated concentrations.",
                    "source": "SCCS",
                    "reference_id": "SCCS/1521/14",  # Placeholder
                    "document_name": "Opinion on Parabens Safety",  # Placeholder
                    "evidence_strength": EvidenceStrength.MEDIUM
                },
                {
                    "exposure_route": ExposureRoute.SKIN,
                    "safe_limit": 0.4,
                    "unit": "%",
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Generally recognized as safe for cosmetic use at regulated concentrations",
                    "source": "FDA",
                    "reference_id": "FDA-CFR-21-175.300",  # Placeholder
                    "document_name": "FDA Code of Federal Regulations - Parabens",  # Placeholder
                    "evidence_strength": EvidenceStrength.HIGH
                }
            ]
        },
        {
            "name": "Caffeine",
            "inci_name": "Caffeine",
            "cas_number": "58-08-2",
            "aliases": ["1,3,7-Trimethylxanthine", "Theine", "Guaranine"],
            "category": "food",
            "evidence_strength": EvidenceStrength.HIGH,
            "confidence": ConfidenceLevel.HIGH,
            "notes": (
                "Natural stimulant found in coffee, tea, and other beverages. "
                "Safe for most adults at moderate consumption (up to 400mg/day). "
                "May cause anxiety, insomnia, or jitteriness in sensitive individuals. "
                "Not recommended for children, pregnant women, or individuals with heart conditions. "
                "Can be absorbed through skin in topical products."
            ),
            "sources": ["EFSA", "FDA", "Health Canada"],
            "safety_profiles": [
                {
                    "exposure_route": ExposureRoute.INGESTION,
                    "safe_limit": 400.0,
                    "unit": "mg/day",
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Safe for most adults at moderate consumption (up to 400mg/day)",
                    "source": "EFSA",
                    "reference_id": "EFSA-Q-2015-00001",  # Placeholder
                    "document_name": "Scientific Opinion on Caffeine Safety",  # Placeholder
                    "evidence_strength": EvidenceStrength.HIGH
                },
                {
                    "exposure_route": ExposureRoute.INGESTION,
                    "safe_limit": 200.0,
                    "unit": "mg/day",
                    "risk_level": RiskLevel.MODERATE,
                    "population_risk": PopulationRisk.PREGNANCY,
                    "summary": "Lower safe limit during pregnancy (200mg/day). Consult healthcare provider.",
                    "source": "Health Canada",
                    "reference_id": "HC-SC-2017-001",  # Placeholder
                    "document_name": "Health Canada Guidance on Caffeine During Pregnancy",  # Placeholder
                    "evidence_strength": EvidenceStrength.HIGH
                },
                {
                    "exposure_route": ExposureRoute.SKIN,
                    "safe_limit": 3.0,
                    "unit": "%",
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Generally safe for topical use in cosmetic products",
                    "source": "SCCS",
                    "reference_id": "SCCS/1456/11",  # Placeholder
                    "document_name": "Opinion on Caffeine in Cosmetics",  # Placeholder
                    "evidence_strength": EvidenceStrength.MEDIUM
                }
            ]
        },
        {
            "name": "Phosphoric Acid",
            "inci_name": "Phosphoric Acid",
            "cas_number": "7664-38-2",
            "aliases": ["Orthophosphoric Acid", "E338"],
            "category": "food",
            "evidence_strength": EvidenceStrength.HIGH,
            "confidence": ConfidenceLevel.HIGH,
            "notes": (
                "Acidulant and pH adjuster used in food and beverages. "
                "Approved food additive (E338). "
                "High concentrations can cause tooth enamel erosion and irritation. "
                "Safe at low concentrations in food products. "
                "Avoid direct contact with skin or eyes at high concentrations."
            ),
            "sources": ["EFSA", "FDA", "JECFA"],
            "safety_profiles": [
                {
                    "exposure_route": ExposureRoute.INGESTION,
                    "safe_limit": None,
                    "unit": None,
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Approved food additive (E338). Generally safe at concentrations used in food products.",
                    "source": "EFSA",
                    "reference_id": "EFSA-Q-2010-00045",  # Placeholder
                    "document_name": "Scientific Opinion on Phosphoric Acid (E338)",  # Placeholder
                    "evidence_strength": EvidenceStrength.HIGH
                },
                {
                    "exposure_route": ExposureRoute.INGESTION,
                    "safe_limit": None,
                    "unit": None,
                    "risk_level": RiskLevel.MODERATE,
                    "population_risk": PopulationRisk.CHILDREN,
                    "summary": "May contribute to tooth enamel erosion in children when consumed frequently in acidic beverages",
                    "source": "EFSA",
                    "reference_id": "EFSA-Q-2010-00045",  # Placeholder
                    "document_name": "Scientific Opinion on Phosphoric Acid (E338)",  # Placeholder
                    "evidence_strength": EvidenceStrength.MEDIUM
                },
                {
                    "exposure_route": ExposureRoute.SKIN,
                    "safe_limit": 1.0,
                    "unit": "%",
                    "risk_level": RiskLevel.MODERATE,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Can cause skin irritation at high concentrations. Safe at low concentrations in cosmetic products.",
                    "source": "SCCS",
                    "reference_id": "SCCS/1345/10",  # Placeholder
                    "document_name": "Opinion on Phosphoric Acid in Cosmetics",  # Placeholder
                    "evidence_strength": EvidenceStrength.MEDIUM
                }
            ]
        },
        {
            "name": "Glycerin",
            "inci_name": "Glycerin",
            "cas_number": "56-81-5",
            "aliases": ["Glycerol", "Glycerine", "1,2,3-Propanetriol"],
            "category": "cosmetic",
            "evidence_strength": EvidenceStrength.HIGH,
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Humectant commonly used in cosmetics and food. Generally recognized as safe. Low risk of irritation.",
            "sources": ["FDA", "EFSA", "CIR"],
            "safety_profiles": [
                {
                    "exposure_route": ExposureRoute.SKIN,
                    "safe_limit": None,
                    "unit": None,
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Generally recognized as safe for cosmetic use. Low risk of irritation.",
                    "source": "CIR",
                    "reference_id": "CIR-2019-002",  # Placeholder
                    "document_name": "Final Report on Glycerin Safety Assessment",  # Placeholder
                    "evidence_strength": EvidenceStrength.HIGH
                },
                {
                    "exposure_route": ExposureRoute.INGESTION,
                    "safe_limit": None,
                    "unit": None,
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Generally recognized as safe (GRAS) for food use.",
                    "source": "FDA",
                    "reference_id": "FDA-CFR-21-184.1320",  # Placeholder
                    "document_name": "FDA GRAS Notice for Glycerin",  # Placeholder
                    "evidence_strength": EvidenceStrength.HIGH
                }
            ]
        },
        {
            "name": "Water",
            "inci_name": "Aqua",
            "cas_number": "7732-18-5",
            "aliases": [
                "Aqua", "H2O", "Purified Water", "Distilled Water", "Deionized Water",
                "Eau", "Water (Aqua)", "Aqua (Water)", "Demineralized Water",
                "Sterile Water", "Spring Water", "Mineral Water"
            ],
            "category": "cosmetic",
            "evidence_strength": EvidenceStrength.HIGH,
            "confidence": ConfidenceLevel.HIGH,
            "notes": (
                "Universal solvent and base ingredient. Essential for life and safe for all populations. "
                "No known safety concerns at any concentration. Used as a carrier and diluent in cosmetic, "
                "food, and pharmaceutical products. Pure water is non-irritating and non-toxic."
            ),
            "sources": ["FDA", "EFSA", "WHO", "CIR", "USP"],
            "safety_profiles": [
                {
                    "exposure_route": ExposureRoute.SKIN,
                    "safe_limit": None,
                    "unit": None,
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Completely safe for topical use. No known adverse effects. Essential component of cosmetic formulations.",
                    "source": "CIR",
                    "reference_id": "CIR-2021-001",  # Placeholder
                    "document_name": "Final Report on Water Safety Assessment",  # Placeholder
                    "evidence_strength": EvidenceStrength.HIGH
                },
                {
                    "exposure_route": ExposureRoute.INGESTION,
                    "safe_limit": None,
                    "unit": None,
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.GENERAL,
                    "summary": "Essential for life. Safe for consumption at any reasonable quantity. No known toxicity.",
                    "source": "WHO",
                    "reference_id": "WHO-GDWQ-2021",  # Placeholder
                    "document_name": "WHO Guidelines for Drinking-water Quality",  # Placeholder
                    "evidence_strength": EvidenceStrength.HIGH
                },
                {
                    "exposure_route": ExposureRoute.INGESTION,
                    "safe_limit": None,
                    "unit": None,
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.PREGNANCY,
                    "summary": "Safe during pregnancy. Essential for hydration and health.",
                    "source": "WHO",
                    "reference_id": "WHO-GDWQ-2021",  # Placeholder
                    "document_name": "WHO Guidelines for Drinking-water Quality",  # Placeholder
                    "evidence_strength": EvidenceStrength.HIGH
                },
                {
                    "exposure_route": ExposureRoute.INGESTION,
                    "safe_limit": None,
                    "unit": None,
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.CHILDREN,
                    "summary": "Safe for children. Essential for hydration and development.",
                    "source": "WHO",
                    "reference_id": "WHO-GDWQ-2021",  # Placeholder
                    "document_name": "WHO Guidelines for Drinking-water Quality",  # Placeholder
                    "evidence_strength": EvidenceStrength.HIGH
                },
                {
                    "exposure_route": ExposureRoute.SKIN,
                    "safe_limit": None,
                    "unit": None,
                    "risk_level": RiskLevel.LOW,
                    "population_risk": PopulationRisk.SENSITIVE_SKIN,
                    "summary": "Completely safe for sensitive skin. Non-irritating and hypoallergenic.",
                    "source": "CIR",
                    "reference_id": "CIR-2021-001",  # Placeholder
                    "document_name": "Final Report on Water Safety Assessment",  # Placeholder
                    "evidence_strength": EvidenceStrength.HIGH
                }
            ]
        }
    ]
    
    created_count = 0
    updated_count = 0
    skipped_count = 0
    
    for ing_data in ingredients_data:
        # Check if ingredient already exists (by name or INCI name)
        existing = db.query(Ingredient).filter(
            (Ingredient.name == ing_data["name"]) |
            (Ingredient.inci_name == ing_data.get("inci_name"))
        ).first()
        
        if existing:
            # Update existing ingredient with new fields if they're missing
            if not existing.aliases and ing_data.get("aliases"):
                existing.aliases = ing_data["aliases"]
            if not existing.confidence and ing_data.get("confidence"):
                existing.confidence = ing_data["confidence"]
            if not existing.sources and ing_data.get("sources"):
                existing.sources = ing_data["sources"]
            if not existing.notes and ing_data.get("notes"):
                existing.notes = ing_data["notes"]
            
            # Update safety profiles
            for profile_data in ing_data.get("safety_profiles", []):
                # Check if profile already exists
                existing_profile = db.query(IngredientSafety).filter(
                    IngredientSafety.ingredient_id == existing.id,
                    IngredientSafety.exposure_route == profile_data["exposure_route"]
                ).first()
                
                if not existing_profile:
                    safety_profile = IngredientSafety(
                        ingredient_id=existing.id,
                        exposure_route=profile_data["exposure_route"],
                        safe_limit=profile_data.get("safe_limit"),
                        unit=profile_data.get("unit"),
                        risk_level=profile_data["risk_level"],
                        population_risk=profile_data["population_risk"],
                        summary=profile_data.get("summary"),
                        source=profile_data.get("source"),
                        reference_id=profile_data.get("reference_id"),
                        document_name=profile_data.get("document_name"),
                        evidence_strength=profile_data.get("evidence_strength")
                    )
                    db.add(safety_profile)
            
            updated_count += 1
            print(f"🔄 Updated {ing_data['name']} with {len(ing_data.get('safety_profiles', []))} safety profile(s)")
            continue
        
        # Create new ingredient
        ingredient = Ingredient(
            name=ing_data["name"],
            inci_name=ing_data.get("inci_name"),
            cas_number=ing_data.get("cas_number"),
            aliases=ing_data.get("aliases"),
            category=ing_data.get("category"),
            evidence_strength=ing_data.get("evidence_strength"),
            confidence=ing_data.get("confidence"),
            notes=ing_data.get("notes"),
            sources=ing_data.get("sources")
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
                source=profile_data.get("source"),
                reference_id=profile_data.get("reference_id"),
                document_name=profile_data.get("document_name"),
                evidence_strength=profile_data.get("evidence_strength")
            )
            db.add(safety_profile)
        
        created_count += 1
        print(f"✅ Created {ing_data['name']} with {len(ing_data.get('safety_profiles', []))} safety profile(s)")
    
    # Commit all changes
    db.commit()
    
    print(f"\n📊 Summary:")
    print(f"   Created: {created_count} ingredients")
    print(f"   Updated: {updated_count} ingredients")
    print(f"   Skipped: {skipped_count} ingredients")
    print(f"   Total: {created_count + updated_count + skipped_count} ingredients processed")


if __name__ == "__main__":
    print("🌱 Seeding ingredient knowledge base with curated ingredients...\n")
    
    db = SessionLocal()
    try:
        seed_ingredient_knowledge_base(db)
        print("\n✨ Seeding completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()
