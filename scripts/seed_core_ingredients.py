"""Script to seed the core ingredient knowledge base with 30-50 common ingredients."""
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
import logging
from app.database import SessionLocal, engine, Base
from app.models import (
    Ingredient, IngredientSafety,
    EvidenceStrength, ExposureRoute, RiskLevel, PopulationRisk, ConfidenceLevel
)

logger = logging.getLogger(__name__)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)


def seed_core_ingredients(db: Session):
    """Seed the ingredient knowledge base with 30-50 common food and cosmetic ingredients."""
    
    # Core ingredients with comprehensive data
    ingredients_data = [
        # === FOOD INGREDIENTS ===
        {
            "name": "Water",
            "inci_name": "Aqua",
            "aliases": ["Aqua", "Purified Water", "Distilled Water", "Deionized Water", "H2O"],
            "category": "food",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Essential and safe ingredient. No known safety concerns.",
            "sources": ["FDA", "EFSA"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.INGESTION,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "Water is essential for life and has no known safety concerns.",
                "source": "FDA",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Sugar",
            "inci_name": "Sucrose",
            "aliases": ["Sucrose", "Cane Sugar", "Beet Sugar", "Table Sugar"],
            "category": "food",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Generally recognized as safe (GRAS). Excessive consumption may contribute to health issues.",
            "sources": ["FDA", "EFSA"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.INGESTION,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "GRAS ingredient. Safe for consumption in normal amounts.",
                "source": "FDA",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Citric Acid",
            "inci_name": "Citric Acid",
            "cas_number": "77-92-9",
            "aliases": ["E330", "2-Hydroxy-1,2,3-propanetricarboxylic Acid"],
            "category": "food",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Natural preservative and flavoring agent. GRAS. May cause mild irritation in sensitive individuals at high concentrations.",
            "sources": ["FDA", "EFSA"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.INGESTION,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "GRAS preservative and acidulant. Safe for consumption.",
                "source": "FDA",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Sodium Chloride",
            "inci_name": "Sodium Chloride",
            "cas_number": "7647-14-5",
            "aliases": ["Salt", "Table Salt", "NaCl", "Sea Salt"],
            "category": "food",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Essential nutrient. GRAS. Excessive consumption may contribute to hypertension.",
            "sources": ["FDA", "EFSA"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.INGESTION,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "GRAS. Essential nutrient. Safe in normal dietary amounts.",
                "source": "FDA",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Carbon Dioxide",
            "inci_name": "Carbon Dioxide",
            "cas_number": "124-38-9",
            "aliases": ["CO2", "E290"],
            "category": "food",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Used as carbonating agent in beverages. GRAS. No known safety concerns at food concentrations.",
            "sources": ["FDA", "EFSA"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.INGESTION,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "GRAS carbonating agent. Safe in food products.",
                "source": "FDA",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Caffeine",
            "inci_name": "Caffeine",
            "cas_number": "58-08-2",
            "aliases": ["1,3,7-Trimethylxanthine", "Guaranine", "Theine"],
            "category": "food",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Stimulant found in coffee, tea, and energy drinks. Safe in moderate amounts (up to 400mg/day for adults). May cause sensitivity in some individuals. Not recommended for children or pregnant women in high amounts.",
            "sources": ["EFSA", "FDA"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.INGESTION,
                "safe_limit": 400.0,
                "unit": "mg/day",
                "risk_level": RiskLevel.MODERATE,
                "population_risk": PopulationRisk.CHILDREN,
                "summary": "Safe in moderate amounts for adults. Limit consumption in children and during pregnancy.",
                "source": "EFSA",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Phosphoric Acid",
            "inci_name": "Phosphoric Acid",
            "cas_number": "7664-38-2",
            "aliases": ["Orthophosphoric Acid", "E338"],
            "category": "food",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Acidulant used in soft drinks. GRAS. May contribute to dental erosion with frequent consumption.",
            "sources": ["FDA", "EFSA"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.INGESTION,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "GRAS acidulant. May contribute to dental erosion with excessive consumption.",
                "source": "FDA",
                "evidence_strength": EvidenceStrength.MEDIUM
            }]
        },
        {
            "name": "Sodium Benzoate",
            "inci_name": "Sodium Benzoate",
            "cas_number": "532-32-1",
            "aliases": ["E211", "Benzoate of Soda"],
            "category": "food",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Preservative. GRAS. May form benzene when combined with ascorbic acid and exposed to heat/light. Generally safe at approved levels.",
            "sources": ["FDA", "EFSA"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.INGESTION,
                "safe_limit": 0.1,
                "unit": "%",
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "GRAS preservative. Safe at approved concentrations.",
                "source": "FDA",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Potassium Sorbate",
            "inci_name": "Potassium Sorbate",
            "cas_number": "24634-61-5",
            "aliases": ["E202", "Sorbic Acid Potassium Salt"],
            "category": "food",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Preservative. GRAS. Generally safe. May cause mild irritation in sensitive individuals.",
            "sources": ["FDA", "EFSA"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.INGESTION,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "GRAS preservative. Safe for consumption.",
                "source": "FDA",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Ascorbic Acid",
            "inci_name": "Ascorbic Acid",
            "cas_number": "50-81-7",
            "aliases": ["Vitamin C", "E300", "L-Ascorbic Acid"],
            "category": "food",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Essential vitamin and antioxidant. GRAS. Safe and beneficial in normal amounts.",
            "sources": ["FDA", "EFSA"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.INGESTION,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "Essential nutrient. GRAS. Safe and beneficial.",
                "source": "FDA",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Natural Flavors",
            "inci_name": "Natural Flavors",
            "aliases": ["Natural Flavoring", "Natural Flavor", "Flavoring"],
            "category": "food",
            "confidence": ConfidenceLevel.MEDIUM,
            "notes": "Complex mixture of flavor compounds derived from natural sources. GRAS. Composition varies by product. Generally safe.",
            "sources": ["FDA"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.INGESTION,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "GRAS flavoring agents. Generally safe.",
                "source": "FDA",
                "evidence_strength": EvidenceStrength.MEDIUM
            }]
        },
        {
            "name": "Artificial Flavors",
            "inci_name": "Artificial Flavors",
            "aliases": ["Artificial Flavoring", "Artificial Flavor"],
            "category": "food",
            "confidence": ConfidenceLevel.MEDIUM,
            "notes": "Synthetic flavor compounds. GRAS. Generally safe at approved levels.",
            "sources": ["FDA"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.INGESTION,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "GRAS synthetic flavoring agents. Generally safe.",
                "source": "FDA",
                "evidence_strength": EvidenceStrength.MEDIUM
            }]
        },
        {
            "name": "Caramel Color",
            "inci_name": "Caramel Color",
            "aliases": ["Caramel", "E150", "Caramel Coloring"],
            "category": "food",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Food coloring made from heated sugar. GRAS. Some types (E150c, E150d) may contain 4-MEI, but levels in food are considered safe.",
            "sources": ["FDA", "EFSA"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.INGESTION,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "GRAS food coloring. Safe at approved levels.",
                "source": "FDA",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Acesulfame Potassium",
            "inci_name": "Acesulfame Potassium",
            "cas_number": "55589-62-3",
            "aliases": ["Acesulfame K", "Ace-K", "E950"],
            "category": "food",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Artificial sweetener. Approved for use. Generally safe. Some individuals may experience sensitivity.",
            "sources": ["FDA", "EFSA"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.INGESTION,
                "safe_limit": 9.0,
                "unit": "mg/kg body weight/day",
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "Approved artificial sweetener. Safe at acceptable daily intake levels.",
                "source": "EFSA",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Sucralose",
            "inci_name": "Sucralose",
            "cas_number": "56038-13-2",
            "aliases": ["E955", "Trichlorogalactosucrose"],
            "category": "food",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Artificial sweetener. Approved for use. Generally safe. Some studies suggest potential effects on gut microbiota at high doses.",
            "sources": ["FDA", "EFSA"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.INGESTION,
                "safe_limit": 15.0,
                "unit": "mg/kg body weight/day",
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "Approved artificial sweetener. Safe at acceptable daily intake levels.",
                "source": "EFSA",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        
        # === COSMETIC INGREDIENTS ===
        {
            "name": "Glycerin",
            "inci_name": "Glycerin",
            "cas_number": "56-81-5",
            "aliases": ["Glycerol", "Glycerine", "1,2,3-Propanetriol"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Humectant and moisturizer. GRAS. Very safe. Used in food and cosmetics. No known safety concerns.",
            "sources": ["FDA", "CIR", "SCCS"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "Safe humectant. No known safety concerns.",
                "source": "CIR",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Sodium Lauryl Sulfate",
            "inci_name": "Sodium Lauryl Sulfate",
            "cas_number": "151-21-3",
            "aliases": ["SLS", "Sodium Dodecyl Sulfate", "SDS"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Surfactant. Can cause skin irritation and dryness, especially in sensitive individuals. Safe at concentrations below 1% for most users.",
            "sources": ["SCCS", "CIR"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "safe_limit": 1.0,
                "unit": "%",
                "risk_level": RiskLevel.MODERATE,
                "population_risk": PopulationRisk.SENSITIVE_SKIN,
                "summary": "Can cause skin irritation, especially in sensitive individuals at concentrations above 1%",
                "source": "SCCS",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Fragrance",
            "inci_name": "Parfum",
            "aliases": ["Parfum", "Aroma", "Fragrance Blend", "Perfume"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.MEDIUM,
            "notes": "Complex mixture of fragrance compounds. May contain allergens. Can cause skin irritation and allergic reactions in sensitive individuals. Not required to disclose specific components.",
            "sources": ["SCCS", "IFRA"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "risk_level": RiskLevel.MODERATE,
                "population_risk": PopulationRisk.SENSITIVE_SKIN,
                "summary": "May cause skin irritation and allergic reactions in sensitive individuals.",
                "source": "SCCS",
                "evidence_strength": EvidenceStrength.MEDIUM
            }]
        },
        {
            "name": "Parabens",
            "inci_name": "Parabens",
            "aliases": ["Methylparaben", "Propylparaben", "Butylparaben", "Ethylparaben", "Paraben"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Preservative family. Generally safe at approved concentrations. Some controversy regarding potential endocrine effects, but regulatory bodies consider them safe. Some consumers prefer paraben-free products.",
            "sources": ["SCCS", "FDA", "CIR"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "safe_limit": 0.4,
                "unit": "%",
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "Safe preservative at approved concentrations. Regulatory bodies consider them safe for use.",
                "source": "SCCS",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Dimethicone",
            "inci_name": "Dimethicone",
            "cas_number": "9006-65-9",
            "aliases": ["Polydimethylsiloxane", "PDMS", "Silicone"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Silicone-based emollient. Generally safe. Non-comedogenic. May cause mild irritation in some individuals.",
            "sources": ["CIR", "SCCS"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "Safe emollient. Generally well-tolerated.",
                "source": "CIR",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Titanium Dioxide",
            "inci_name": "Titanium Dioxide",
            "cas_number": "13463-67-7",
            "aliases": ["TiO2", "CI 77891", "Titanium(IV) Oxide"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "UV filter and white pigment. Generally safe for topical use. Inhalation of nanoparticles may be a concern, but topical application is considered safe.",
            "sources": ["SCCS", "FDA"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "Safe UV filter and pigment for topical use.",
                "source": "SCCS",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Zinc Oxide",
            "inci_name": "Zinc Oxide",
            "cas_number": "1314-13-2",
            "aliases": ["ZnO", "CI 77947"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "UV filter and skin protectant. Generally safe. May cause mild irritation in some individuals.",
            "sources": ["SCCS", "FDA"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "Safe UV filter and skin protectant.",
                "source": "SCCS",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Retinol",
            "inci_name": "Retinol",
            "cas_number": "68-26-8",
            "aliases": ["Vitamin A", "Vitamin A Alcohol"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Vitamin A derivative. Can cause skin irritation, dryness, and increased sun sensitivity. Not recommended during pregnancy. Start with low concentrations.",
            "sources": ["SCCS", "CIR"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "safe_limit": 0.3,
                "unit": "%",
                "risk_level": RiskLevel.MODERATE,
                "population_risk": PopulationRisk.PREGNANCY,
                "summary": "Can cause skin irritation and increased sun sensitivity. Avoid during pregnancy.",
                "source": "SCCS",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Salicylic Acid",
            "inci_name": "Salicylic Acid",
            "cas_number": "77-69-4",
            "aliases": ["BHA", "2-Hydroxybenzoic Acid"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Beta hydroxy acid (BHA). Exfoliant. Can cause skin irritation, especially in sensitive individuals. Not recommended during pregnancy. Safe at concentrations below 2%.",
            "sources": ["SCCS", "CIR"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "safe_limit": 2.0,
                "unit": "%",
                "risk_level": RiskLevel.MODERATE,
                "population_risk": PopulationRisk.SENSITIVE_SKIN,
                "summary": "Exfoliant. Can cause irritation. Avoid during pregnancy.",
                "source": "SCCS",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Niacinamide",
            "inci_name": "Niacinamide",
            "cas_number": "98-92-0",
            "aliases": ["Nicotinamide", "Vitamin B3"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Vitamin B3 derivative. Generally safe and well-tolerated. May cause mild flushing in some individuals at high concentrations.",
            "sources": ["CIR", "SCCS"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "Safe and well-tolerated ingredient.",
                "source": "CIR",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Hyaluronic Acid",
            "inci_name": "Hyaluronic Acid",
            "cas_number": "9004-61-9",
            "aliases": ["HA", "Sodium Hyaluronate"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Humectant and moisturizer. Very safe. Naturally occurring in skin. No known safety concerns.",
            "sources": ["CIR", "SCCS"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "Safe humectant. No known safety concerns.",
                "source": "CIR",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Ceramides",
            "inci_name": "Ceramides",
            "aliases": ["Ceramide NP", "Ceramide AP", "Ceramide EOP"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Lipid component of skin barrier. Very safe. Naturally occurring in skin. No known safety concerns.",
            "sources": ["CIR"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "Safe skin barrier component. No known safety concerns.",
                "source": "CIR",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Peptides",
            "inci_name": "Peptides",
            "aliases": ["Palmitoyl Pentapeptide", "Copper Peptides", "Peptide Complex"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.MEDIUM,
            "notes": "Amino acid chains. Generally safe. Limited long-term safety data. Well-tolerated in most individuals.",
            "sources": ["CIR"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "Generally safe. Limited long-term data available.",
                "source": "CIR",
                "evidence_strength": EvidenceStrength.MEDIUM
            }]
        },
        {
            "name": "Benzoyl Peroxide",
            "inci_name": "Benzoyl Peroxide",
            "cas_number": "94-36-0",
            "aliases": ["BPO", "Benzoyl Peroxide"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Acne treatment. Can cause significant skin irritation, dryness, and bleaching of fabrics. Start with low concentrations (2.5-5%).",
            "sources": ["FDA", "CIR"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "safe_limit": 10.0,
                "unit": "%",
                "risk_level": RiskLevel.MODERATE,
                "population_risk": PopulationRisk.SENSITIVE_SKIN,
                "summary": "Can cause significant skin irritation. Use with caution.",
                "source": "FDA",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Alcohol",
            "inci_name": "Alcohol",
            "cas_number": "64-17-5",
            "aliases": ["Ethanol", "Ethyl Alcohol", "Denatured Alcohol"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Solvent and preservative. Can cause skin dryness and irritation, especially at high concentrations. Avoid in products for sensitive or dry skin.",
            "sources": ["CIR", "SCCS"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "safe_limit": 10.0,
                "unit": "%",
                "risk_level": RiskLevel.MODERATE,
                "population_risk": PopulationRisk.SENSITIVE_SKIN,
                "summary": "Can cause skin dryness and irritation at high concentrations.",
                "source": "CIR",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Phenoxyethanol",
            "inci_name": "Phenoxyethanol",
            "cas_number": "122-99-6",
            "aliases": ["2-Phenoxyethanol", "Ethylene Glycol Phenyl Ether"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Preservative. Generally safe at approved concentrations (up to 1%). May cause mild irritation in sensitive individuals.",
            "sources": ["SCCS", "CIR"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "safe_limit": 1.0,
                "unit": "%",
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "Safe preservative at approved concentrations.",
                "source": "SCCS",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Cocamidopropyl Betaine",
            "inci_name": "Cocamidopropyl Betaine",
            "cas_number": "61789-40-0",
            "aliases": ["CAPB", "Coco-Betaine"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Surfactant. Generally safe. May cause mild irritation in sensitive individuals. Can contain trace amounts of amidoamine which may cause allergic reactions.",
            "sources": ["CIR", "SCCS"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.SENSITIVE_SKIN,
                "summary": "Generally safe surfactant. May cause irritation in sensitive individuals.",
                "source": "CIR",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Sodium Hydroxide",
            "inci_name": "Sodium Hydroxide",
            "cas_number": "1310-73-2",
            "aliases": ["Lye", "Caustic Soda", "NaOH"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "pH adjuster. Highly alkaline. Can cause severe burns at high concentrations. Safe when properly formulated and neutralized in final product.",
            "sources": ["CIR", "SCCS"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "safe_limit": 0.5,
                "unit": "%",
                "risk_level": RiskLevel.MODERATE,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "pH adjuster. Safe when properly formulated in final product.",
                "source": "CIR",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Citric Acid",
            "inci_name": "Citric Acid",
            "cas_number": "77-92-9",
            "aliases": ["E330", "2-Hydroxy-1,2,3-propanetricarboxylic Acid"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "pH adjuster and chelating agent. Generally safe. May cause mild irritation in sensitive individuals at high concentrations.",
            "sources": ["CIR", "SCCS"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "Safe pH adjuster. Generally well-tolerated.",
                "source": "CIR",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Tocopherol",
            "inci_name": "Tocopherol",
            "cas_number": "59-02-9",
            "aliases": ["Vitamin E", "Alpha-Tocopherol", "d-alpha-Tocopherol"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Antioxidant. Generally safe. May cause mild irritation in some individuals. Beneficial for skin health.",
            "sources": ["CIR", "SCCS"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "Safe antioxidant. Beneficial for skin health.",
                "source": "CIR",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Allantoin",
            "inci_name": "Allantoin",
            "cas_number": "97-59-6",
            "aliases": ["5-Ureidohydantoin"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Skin protectant and moisturizer. Very safe. No known safety concerns.",
            "sources": ["CIR"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "Safe skin protectant. No known safety concerns.",
                "source": "CIR",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Panthenol",
            "inci_name": "Panthenol",
            "cas_number": "81-13-0",
            "aliases": ["Provitamin B5", "D-Panthenol"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Provitamin B5. Very safe. Moisturizing and soothing. No known safety concerns.",
            "sources": ["CIR", "SCCS"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "Safe moisturizing ingredient. No known safety concerns.",
                "source": "CIR",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Aloe Vera",
            "inci_name": "Aloe Barbadensis Leaf Juice",
            "aliases": ["Aloe", "Aloe Barbadensis", "Aloe Vera Gel"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Plant extract. Generally safe. Soothing and moisturizing. May cause allergic reactions in sensitive individuals.",
            "sources": ["CIR"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.SENSITIVE_SKIN,
                "summary": "Generally safe plant extract. May cause allergic reactions in sensitive individuals.",
                "source": "CIR",
                "evidence_strength": EvidenceStrength.MEDIUM
            }]
        },
        {
            "name": "Shea Butter",
            "inci_name": "Butyrospermum Parkii Butter",
            "aliases": ["Shea", "Karite Butter"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Natural emollient. Very safe. No known safety concerns. May cause allergic reactions in individuals with nut allergies.",
            "sources": ["CIR"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "Safe natural emollient. May cause reactions in individuals with nut allergies.",
                "source": "CIR",
                "evidence_strength": EvidenceStrength.MEDIUM
            }]
        },
        {
            "name": "Jojoba Oil",
            "inci_name": "Simmondsia Chinensis Seed Oil",
            "aliases": ["Jojoba", "Jojoba Seed Oil"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Natural emollient. Very safe. Non-comedogenic. No known safety concerns.",
            "sources": ["CIR"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "Safe natural emollient. No known safety concerns.",
                "source": "CIR",
                "evidence_strength": EvidenceStrength.HIGH
            }]
        },
        {
            "name": "Coconut Oil",
            "inci_name": "Cocos Nucifera Oil",
            "aliases": ["Coconut", "Coco Oil"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Natural emollient. Generally safe. May be comedogenic for some individuals. May cause allergic reactions in sensitive individuals.",
            "sources": ["CIR"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "Generally safe natural emollient. May be comedogenic for some.",
                "source": "CIR",
                "evidence_strength": EvidenceStrength.MEDIUM
            }]
        },
        {
            "name": "Argan Oil",
            "inci_name": "Argania Spinosa Kernel Oil",
            "aliases": ["Argan", "Argania Oil"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Natural emollient. Very safe. No known safety concerns.",
            "sources": ["CIR"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.GENERAL,
                "summary": "Safe natural emollient. No known safety concerns.",
                "source": "CIR",
                "evidence_strength": EvidenceStrength.MEDIUM
            }]
        },
        {
            "name": "Tea Tree Oil",
            "inci_name": "Melaleuca Alternifolia Leaf Oil",
            "aliases": ["Tea Tree", "Melaleuca Oil"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Essential oil with antimicrobial properties. Can cause skin irritation and allergic reactions, especially in sensitive individuals. Use with caution. Not recommended for children.",
            "sources": ["CIR"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "safe_limit": 1.0,
                "unit": "%",
                "risk_level": RiskLevel.MODERATE,
                "population_risk": PopulationRisk.SENSITIVE_SKIN,
                "summary": "Can cause skin irritation. Use with caution.",
                "source": "CIR",
                "evidence_strength": EvidenceStrength.MEDIUM
            }]
        },
        {
            "name": "Lavender Oil",
            "inci_name": "Lavandula Angustifolia Oil",
            "aliases": ["Lavender", "Lavender Essential Oil"],
            "category": "cosmetic",
            "confidence": ConfidenceLevel.HIGH,
            "notes": "Essential oil. Generally safe. May cause skin irritation and allergic reactions in sensitive individuals. Some concerns about potential endocrine effects, but evidence is limited.",
            "sources": ["CIR", "IFRA"],
            "safety_profiles": [{
                "exposure_route": ExposureRoute.SKIN,
                "safe_limit": 1.0,
                "unit": "%",
                "risk_level": RiskLevel.LOW,
                "population_risk": PopulationRisk.SENSITIVE_SKIN,
                "summary": "Generally safe essential oil. May cause irritation in sensitive individuals.",
                "source": "IFRA",
                "evidence_strength": EvidenceStrength.MEDIUM
            }]
        },
    ]
    
    # Seed ingredients
    added_count = 0
    skipped_count = 0
    
    for ing_data in ingredients_data:
        # Check if ingredient already exists
        existing = db.query(Ingredient).filter(
            Ingredient.name == ing_data["name"]
        ).first()
        
        if existing:
            logger.info(f"⏭️  Skipping existing ingredient: {ing_data['name']}")
            skipped_count += 1
            continue
        
        # Create ingredient
        ingredient = Ingredient(
            name=ing_data["name"],
            inci_name=ing_data.get("inci_name"),
            cas_number=ing_data.get("cas_number"),
            aliases=ing_data.get("aliases", []),
            category=ing_data.get("category"),
            evidence_strength=ing_data.get("evidence_strength"),
            confidence=ing_data.get("confidence"),
            notes=ing_data.get("notes"),
            sources=ing_data.get("sources", [])
        )
        
        db.add(ingredient)
        db.flush()  # Get the ID
        
        # Add safety profiles
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
        
        added_count += 1
        logger.info(f"✅ Added ingredient: {ing_data['name']}")
    
    db.commit()
    logger.info(f"\n📊 Summary: Added {added_count} ingredients, Skipped {skipped_count} existing ingredients")
    return added_count


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    db = SessionLocal()
    try:
        seed_core_ingredients(db)
        print(f"\n✅ Successfully seeded core ingredient knowledge base!")
    except Exception as e:
        logger.error(f"❌ Error seeding database: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()
