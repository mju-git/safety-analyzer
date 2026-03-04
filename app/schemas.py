"""Pydantic schemas for request/response models."""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.models import Category, EvidenceStrength, ExposureRoute, RiskLevel, PopulationRisk


class ProductResponse(BaseModel):
    """Product response schema."""
    id: int
    barcode: Optional[str] = None
    name: str
    brand: Optional[str] = None
    category: Category
    ingredients_raw: Optional[str] = None
    source: Optional[str] = None
    last_fetched: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class FlaggedIngredient(BaseModel):
    """Flagged ingredient in analysis."""
    name: str
    risk_level: str  # low/moderate/high
    confidence: str  # high/medium/low/unknown
    reason: str
    safe_dosage: Optional[float] = None
    unit: Optional[str] = None
    exposure_context: str
    evidence_source: Optional[str] = None
    notes: Optional[str] = None  # Notes about dosage, formulation, or population sensitivity


class BeneficialIngredient(BaseModel):
    """Beneficial ingredient in analysis."""
    name: str
    benefit: str


class AnalysisExplanation(BaseModel):
    """Detailed explanation of safety analysis."""
    flagged_ingredients: List[FlaggedIngredient] = []
    beneficial_ingredients: List[BeneficialIngredient] = []
    recommendation: str


class AnalysisResponse(BaseModel):
    """Product analysis response schema."""
    product_id: Optional[int] = None  # None for ingredient-only analysis
    safety_score: int  # 0-100
    explanation: Dict[str, Any]  # JSON structure
    computed_at: str
    product_source: Optional[str] = None  # Source of product data (e.g., "openfoodfacts", "manual", "database")


class IngredientSafetyProfile(BaseModel):
    """Individual safety profile for an ingredient."""
    exposure_route: ExposureRoute
    safe_limit: Optional[float] = None
    unit: Optional[str] = None
    risk_level: RiskLevel
    population_risk: PopulationRisk
    summary: Optional[str] = None
    source: Optional[str] = None


class IngredientSafetyResponse(BaseModel):
    """Ingredient safety response schema."""
    ingredient_id: int
    name: str
    inci_name: Optional[str] = None
    cas_number: Optional[str] = None
    category: Optional[str] = None
    evidence_strength: Optional[EvidenceStrength] = None
    notes: Optional[str] = None
    safety_profiles: List[IngredientSafetyProfile] = []
