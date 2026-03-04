"""SQLAlchemy models for the Product Safety Analyzer."""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.database import Base


class Category(str, enum.Enum):
    """Product category enum."""
    FOOD = "food"
    COSMETIC = "cosmetic"
    HOUSEHOLD = "household"
    SUPPLEMENT = "supplement"


class EvidenceStrength(str, enum.Enum):
    """Evidence strength enum."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConfidenceLevel(str, enum.Enum):
    """Confidence level enum for ingredient assessments."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class ExposureRoute(str, enum.Enum):
    """Exposure route enum."""
    SKIN = "skin"
    INGESTION = "ingestion"
    INHALATION = "inhalation"


class RiskLevel(str, enum.Enum):
    """Risk level enum."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class PopulationRisk(str, enum.Enum):
    """Population risk category enum."""
    GENERAL = "general"
    SENSITIVE_SKIN = "sensitive_skin"
    PREGNANCY = "pregnancy"
    CHILDREN = "children"


class Product(Base):
    """Product model."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String, unique=True, nullable=True, index=True)
    name = Column(String, nullable=False, index=True)
    brand = Column(String, nullable=True, index=True)
    category = Column(SQLEnum(Category), nullable=False)
    ingredients_raw = Column(Text, nullable=True)
    source = Column(String, nullable=True)  # e.g., "openfoodfacts", "manual"
    last_fetched = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    product_ingredients = relationship("ProductIngredient", back_populates="product", cascade="all, delete-orphan")
    product_scores = relationship("ProductScore", back_populates="product", cascade="all, delete-orphan")


class Ingredient(Base):
    """Ingredient model - Knowledge base for ingredient safety information."""
    __tablename__ = "ingredients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    inci_name = Column(String, nullable=True, index=True)
    cas_number = Column(String, nullable=True)
    aliases = Column(JSON, nullable=True)  # List of alternative names for lookup
    category = Column(String, nullable=True)  # cosmetic / food / household
    evidence_strength = Column(SQLEnum(EvidenceStrength), nullable=True)
    confidence = Column(SQLEnum(ConfidenceLevel), nullable=True)  # Overall confidence in assessment
    notes = Column(Text, nullable=True)  # Dosage, formulation, population sensitivity notes
    sources = Column(JSON, nullable=True)  # List of authoritative sources (e.g., ["EFSA", "SCCS", "CIR"])
    
    # Relationships
    ingredient_safety = relationship("IngredientSafety", back_populates="ingredient", cascade="all, delete-orphan")
    product_ingredients = relationship("ProductIngredient", back_populates="ingredient")


class IngredientSafety(Base):
    """Ingredient safety profile model."""
    __tablename__ = "ingredient_safety"
    
    id = Column(Integer, primary_key=True, index=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    exposure_route = Column(SQLEnum(ExposureRoute), nullable=False)
    safe_limit = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    risk_level = Column(SQLEnum(RiskLevel), nullable=False)
    population_risk = Column(SQLEnum(PopulationRisk), nullable=False)
    summary = Column(Text, nullable=True)
    source = Column(String, nullable=True)  # e.g., "EFSA", "SCCS", "CIR"
    reference_id = Column(String, nullable=True)  # e.g., "SCCS/1234/12", "EFSA-Q-2020-00123", document ID
    document_name = Column(String, nullable=True)  # e.g., "Opinion on Sodium Lauryl Sulfate", document title
    evidence_strength = Column(SQLEnum(EvidenceStrength), nullable=True)  # Evidence strength for this specific profile
    
    # Relationships
    ingredient = relationship("Ingredient", back_populates="ingredient_safety")


class ProductIngredient(Base):
    """Junction table for products and ingredients."""
    __tablename__ = "product_ingredients"
    
    product_id = Column(Integer, ForeignKey("products.id"), primary_key=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), primary_key=True)
    estimated_concentration = Column(Float, nullable=True)
    
    # Relationships
    product = relationship("Product", back_populates="product_ingredients")
    ingredient = relationship("Ingredient", back_populates="product_ingredients")


class ProductScore(Base):
    """Product safety score model."""
    __tablename__ = "product_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    safety_score = Column(Integer, nullable=False)  # 0-100
    explanation = Column(JSON, nullable=True)  # JSON structure for detailed explanation
    computed_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    product = relationship("Product", back_populates="product_scores")
