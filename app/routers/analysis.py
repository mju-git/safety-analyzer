"""Product analysis router."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import json

from app.database import get_db
from app.models import Product, Ingredient, ProductScore, Category
from app.schemas import ProductResponse, AnalysisResponse, IngredientSafetyResponse
from app.services.safety_engine import SafetyEngine
from app.services.ingredient_normalizer import normalize_ingredients, normalize_and_match_ingredients
from app.services.product_summary_engine import ProductSummaryEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["analysis"])


class UserProfile(BaseModel):
    """User profile for personalized analysis."""
    sensitive_skin: bool = False
    pregnant: bool = False
    child: bool = False


class AnalyzeProductRequest(BaseModel):
    """Request model for product analysis by ID."""
    product_id: int
    user_profile: Optional[UserProfile] = None


class AnalyzeByNameRequest(BaseModel):
    """Request model for product analysis by name."""
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    user_profile: Optional[UserProfile] = None


class AnalyzeByIngredientsRequest(BaseModel):
    """Request model for product analysis by raw ingredient list."""
    ingredients: Union[str, List[str]]  # Accept string (comma-separated) or array
    product_name: Optional[str] = None  # Optional product name for context
    category: Optional[str] = None  # Optional category (food/cosmetic/household/supplement)
    user_profile: Optional[UserProfile] = None


@router.post("/product", response_model=AnalysisResponse)
async def analyze_product(
    request: AnalyzeProductRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze a product by ID.
    Used by web and mobile app.
    
    Returns safety score and detailed analysis using the safety engine.
    """
    product = db.query(Product).filter(Product.id == request.product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Perform analysis using safety engine
    try:
        analysis = _analyze_product(
            db=db,
            product=product,
            user_profile=request.user_profile
        )
        
        # Ensure response has correct structure
        if not isinstance(analysis, dict):
            raise ValueError("Analysis function returned invalid format")
        
        if "explanation" not in analysis:
            analysis["explanation"] = {
                "flagged_ingredients": [],
                "beneficial_ingredients": [],
                "recommendation": "Analysis completed",
                "explanations": []
            }
        
        return analysis
    except Exception as e:
        # Log error and return a safe default response
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing product: {str(e)}"
        )


def _lookup_ingredient_by_name_or_alias(
    db: Session,
    ingredient_name: str
) -> Optional[Ingredient]:
    """
    Look up an ingredient by name or aliases.
    
    Searches:
    1. Exact name match (case-insensitive)
    2. INCI name match (case-insensitive)
    3. Alias match (case-insensitive, checks JSON array)
    
    Returns the first matching ingredient or None.
    """
    # Normalize the search term
    search_term = ingredient_name.strip().lower()
    
    # Try exact name match
    ingredient = db.query(Ingredient).filter(
        Ingredient.name.ilike(search_term)
    ).first()
    
    if ingredient:
        return ingredient
    
    # Try INCI name match
    ingredient = db.query(Ingredient).filter(
        Ingredient.inci_name.ilike(search_term)
    ).first()
    
    if ingredient:
        return ingredient
    
    # Try alias match (check JSON array)
    # Get all ingredients and check their aliases
    all_ingredients = db.query(Ingredient).all()
    for ing in all_ingredients:
        if ing.aliases:
            # Handle both list and JSON string formats
            aliases = ing.aliases
            if isinstance(aliases, str):
                try:
                    aliases = json.loads(aliases)
                except (json.JSONDecodeError, TypeError):
                    continue
            
            if isinstance(aliases, list):
                # Check if search term matches any alias (case-insensitive)
                for alias in aliases:
                    if isinstance(alias, str) and alias.lower() == search_term:
                        return ing
    
    return None


def _find_or_create_product(
    db: Session,
    name: str,
    brand: Optional[str] = None,
    category: Optional[str] = None
) -> Product:
    """
    Find existing product or create a new one if not found.
    
    Searches for product by name (and optionally brand/category).
    If not found, creates a new product with the provided information.
    """
    # Search for product in database
    # Try exact match first, then partial match
    query = db.query(Product)
    
    # Build search conditions
    name_conditions = [
        Product.name.ilike(name),  # Exact match (case-insensitive)
        Product.name.ilike(f"%{name}%")  # Partial match
    ]
    
    if brand:
        # If brand is provided, require brand match
        brand_conditions = [
            Product.brand.ilike(brand),
            Product.brand.ilike(f"%{brand}%")
        ]
        # Combine: (name exact OR name partial) AND (brand exact OR brand partial)
        query = query.filter(
            and_(
                or_(*name_conditions),
                or_(*brand_conditions)
            )
        )
    else:
        # If no brand, just match name
        query = query.filter(or_(*name_conditions))
    
    if category:
        try:
            category_enum = Category(category)
            query = query.filter(Product.category == category_enum)
        except ValueError:
            pass  # Invalid category, ignore
    
    # Order by name (exact matches will naturally come first due to ILIKE ordering)
    query = query.order_by(Product.name)
    
    product = query.first()
    
    # If product not found, create a new one
    if not product:
        # Determine category - use provided or default to 'food'
        if category:
            try:
                category_enum = Category(category)
            except ValueError:
                category_enum = Category.FOOD  # Default to food if invalid
        else:
            category_enum = Category.FOOD  # Default to food if not provided
        
        # Create new product
        product = Product(
            name=name,
            brand=brand,
            category=category_enum,
            source="manual",  # Mark as manually created
            ingredients_raw=None  # Will be populated when external APIs are implemented
        )
        
        db.add(product)
        db.commit()
        db.refresh(product)
    
    return product


def _analyze_product(
    db: Session,
    product: Product,
    user_profile: Optional[UserProfile] = None
) -> Dict[str, Any]:
    """
    Analyze a product and compute safety score using the safety engine.
    
    Steps:
    1. Load product from database (already loaded)
    2. Normalize ingredients from ingredients_raw using ingredient_normalizer
    3. Fetch ingredient safety data from database
    4. Pass structured ingredient data into SafetyEngine
    5. Return explainable safety output
    """
    # Convert user profile to dict if provided
    user_profile_dict = None
    if user_profile:
        user_profile_dict = {
            "sensitive_skin": user_profile.sensitive_skin,
            "pregnant": user_profile.pregnant,
            "child": user_profile.child
        }
    
    # Step 1: Check if product has ingredients_raw
    if not product.ingredients_raw:
        # No ingredients to analyze - return neutral score
        explanation = {
            "flagged_ingredients": [],
            "beneficial_ingredients": [],
            "recommendation": (
                "Product information is limited. "
                "Ingredient list not available. "
                "External API integration pending."
            ),
            "explanations": []
        }
        
        return {
            "product_id": product.id,
            "safety_score": 50,  # Neutral score when no data
            "explanation": explanation,
            "computed_at": datetime.now().isoformat()
        }
    
    # Step 2: Normalize and match ingredients using ingredient_normalizer
    # This returns canonical ingredient IDs with match information
    matched_ingredients = normalize_and_match_ingredients(db, product.ingredients_raw)
    
    if not matched_ingredients:
        # Empty ingredient list after normalization
        explanation = {
            "flagged_ingredients": [],
            "beneficial_ingredients": [],
            "low_concern_ingredients": [],
            "unknown_ingredients": [],
            "recommendation": "No valid ingredients found in product data.",
            "explanations": [],
            "ingredient_summary": {"total": 0, "known_assessed": 0, "known_low_concern": 0, "unknown": 0},
            "overall_confidence": "unknown"
        }
        
        return {
            "product_id": product.id,
            "safety_score": 50,
            "explanation": explanation,
            "computed_at": datetime.now().isoformat()
        }
    
    # Step 3: Fetch ingredient safety data using canonical ingredient IDs
    ingredients_data = []
    
    for match_info in matched_ingredients:
        ingredient_id = match_info.get("ingredient_id")
        canonical_name = match_info.get("canonical_name")
        original_name = match_info.get("original_name")
        is_unknown = match_info.get("is_unknown", False)
        match_type = match_info.get("match_type")
        resolution_state = match_info.get("resolution_state", "unresolved" if is_unknown else "resolved")
        resolution_confidence = match_info.get("confidence", 0.0 if is_unknown else 1.0)
        match_explanation = match_info.get("match_explanation", "")
        
        if ingredient_id and not is_unknown:
            # Look up ingredient by canonical ID
            ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
            
            if ingredient:
                # Get safety profiles for this ingredient
                safety_profiles = ingredient.ingredient_safety
                
                # Get stored confidence, notes, and sources from knowledge base
                # Handle confidence - could be enum or string
                stored_confidence = None
                if ingredient.confidence:
                    if hasattr(ingredient.confidence, 'value'):
                        stored_confidence = ingredient.confidence.value
                    else:
                        stored_confidence = str(ingredient.confidence)
                stored_notes = ingredient.notes
                stored_sources = ingredient.sources
                
                # Handle sources (could be list or JSON string)
                sources_list = stored_sources
                if isinstance(stored_sources, str):
                    try:
                        sources_list = json.loads(stored_sources)
                    except (json.JSONDecodeError, TypeError):
                        sources_list = [stored_sources] if stored_sources else []
                elif stored_sources is None:
                    sources_list = []
                
                if safety_profiles:
                    # Use the first safety profile (could be enhanced to prioritize by exposure route)
                    profile = safety_profiles[0]
                    
                    # Extract evidence information from profile
                    evidence_source = profile.source
                    evidence_reference_id = profile.reference_id if hasattr(profile, 'reference_id') else None
                    evidence_document_name = profile.document_name if hasattr(profile, 'document_name') else None
                    evidence_strength = profile.evidence_strength.value if hasattr(profile, 'evidence_strength') and profile.evidence_strength else None
                    
                    # Use stored confidence if available, otherwise calculate
                    confidence = stored_confidence
                    if not confidence:
                        # Calculate confidence based on available data
                        has_source = bool(profile.source)
                        has_safe_limit = profile.safe_limit is not None
                        has_summary = bool(profile.summary)
                        if has_source and has_safe_limit and has_summary:
                            confidence = "high"
                        elif has_source and (has_safe_limit or has_summary):
                            confidence = "medium"
                        elif has_source or has_summary:
                            confidence = "low"
                        else:
                            confidence = "unknown"
                    
                    # Combine stored notes with profile summary
                    notes = stored_notes if stored_notes else profile.summary
                    if profile.summary and stored_notes and profile.summary not in stored_notes:
                        notes = f"{stored_notes} {profile.summary}"
                    
                    # Combine sources from ingredient and profile
                    all_sources = sources_list.copy() if sources_list else []
                    if profile.source and profile.source not in all_sources:
                        all_sources.append(profile.source)
                    
                    ingredients_data.append({
                        "name": canonical_name or ingredient.name,  # Use canonical name from match
                        "ingredient_id": ingredient_id,  # Include canonical ID
                        "risk_level": profile.risk_level.value if profile.risk_level else "low",
                        "confidence": confidence,
                        "exposure_route": profile.exposure_route.value if profile.exposure_route else "skin",
                        "safe_limit": profile.safe_limit,
                        "unit": profile.unit,
                        "estimated_concentration": None,  # Not available from raw ingredients
                        "population_risk": profile.population_risk.value if profile.population_risk else "general",
                        "summary": profile.summary,
                        "source": profile.source,
                        "sources": all_sources,  # List of all sources
                        "notes": notes,  # Combined notes from knowledge base
                        "is_unknown": False,
                        "match_type": match_type,  # Track how ingredient was matched
                        "resolution_state": resolution_state,  # resolved, resolved_inferred, or unresolved
                        "resolution_confidence": resolution_confidence,  # Confidence in resolution (0.0-1.0)
                        "match_explanation": match_explanation,  # Explanation of how match was made
                        # Evidence-backed risk attribution
                        "evidence_source": evidence_source,
                        "evidence_reference_id": evidence_reference_id,
                        "evidence_document_name": evidence_document_name,
                        "evidence_strength": evidence_strength
                    })
                else:
                    # Ingredient found in knowledge base but no safety profiles
                    # Use stored confidence or default to low
                    confidence = stored_confidence if stored_confidence else "low"
                    
                    ingredients_data.append({
                        "name": canonical_name or ingredient.name,  # Use canonical name from match
                        "ingredient_id": ingredient_id,  # Include canonical ID
                        "risk_level": "low",  # Conservative default
                        "confidence": confidence,
                        "exposure_route": "skin",
                        "safe_limit": None,
                        "unit": None,
                        "estimated_concentration": None,
                        "population_risk": "general",
                        "summary": stored_notes or "Ingredient found in knowledge base but no detailed safety profile available",
                        "source": sources_list[0] if sources_list else None,
                        "sources": sources_list,
                        "notes": stored_notes,
                        "is_unknown": False,
                        "match_type": match_type,  # Track how ingredient was matched
                        "resolution_state": resolution_state,  # resolved, resolved_inferred, or unresolved
                        "resolution_confidence": resolution_confidence,  # Confidence in resolution (0.0-1.0)
                        "match_explanation": match_explanation  # Explanation of how match was made
                    })
            else:
                # Ingredient ID was found but ingredient doesn't exist (shouldn't happen)
                ingredients_data.append({
                    "name": original_name or canonical_name or "Unknown",
                    "ingredient_id": None,  # No valid ID
                    "risk_level": "unknown",
                    "confidence": "unknown",
                    "exposure_route": "skin",
                    "safe_limit": None,
                    "unit": None,
                    "estimated_concentration": None,
                    "population_risk": "general",
                    "summary": "Ingredient ID found but ingredient record missing.",
                    "source": None,
                    "sources": [],
                    "notes": "Ingredient not found in knowledge base. Safety data unavailable.",
                    "is_unknown": True,
                    "match_type": None,
                    "resolution_state": "unresolved",
                    "resolution_confidence": 0.0,
                    "match_explanation": match_explanation or f"'{original_name}' was not found in the safety knowledge base."
                })
        else:
            # Ingredient not found in knowledge base - explicitly mark as unresolved
            ingredients_data.append({
                "name": original_name or "Unknown",
                "ingredient_id": None,  # No match found
                "risk_level": "unknown",  # Unknown risk level for unresolved ingredients
                "confidence": "unknown",
                "exposure_route": "skin",
                "safe_limit": None,
                "unit": None,
                "estimated_concentration": None,
                "population_risk": "general",
                "summary": "Ingredient not found in safety knowledge base. Assessment based on limited information.",
                "source": None,
                "sources": [],
                "notes": "Ingredient not found in knowledge base. Safety data unavailable.",
                "is_unknown": True,
                "match_type": None,
                "resolution_state": "unresolved",
                "resolution_confidence": 0.0,
                "match_explanation": match_explanation or f"'{original_name}' was not found in the safety knowledge base."
            })
    
    # Step 4: Pass structured ingredient data into SafetyEngine
    safety_engine = SafetyEngine()
    analysis_result = safety_engine.analyze(
        ingredients=ingredients_data,
        user_profile=user_profile_dict
    )
    
    # Step 5: Format and return explainable safety output
    # Format flagged ingredients to match schema with new fields
    flagged_ingredients = []
    for ing in analysis_result.get("flagged_ingredients", []):
        # Build reason from risk level and explanation
        reason_parts = []
        risk_level = ing.get("risk_level", "unknown")
        
        if ing.get("is_unknown") or risk_level == "unknown":
            reason_parts.append("Unknown ingredient - not found in safety database")
        else:
            reason_parts.append(f"{risk_level} risk level")
            if ing.get("explanation"):
                reason_parts.append(ing.get("explanation"))
        
        if ing.get("dosage_exceeded"):
            reason_parts.append("(concentration exceeds safe limit)")
        
        reason = ". ".join(reason_parts) if reason_parts else "Safety concern identified"
        
        # Get sources from safety engine assessment
        sources = ing.get("sources", [])
        primary_source = ing.get("source")
        if primary_source and primary_source not in sources:
            sources.insert(0, primary_source)
        
        flagged_ingredients.append({
            "name": ing.get("name", ""),
            "risk_level": ing.get("risk_level", "unknown"),  # Preserve unknown risk level
            "confidence": ing.get("confidence", "unknown"),
            "reason": reason,
            "safe_dosage": ing.get("safe_limit"),
            "unit": ing.get("unit"),  # Unit is preserved from safety engine
            "exposure_context": f"Used in {product.category.value} products",
            "evidence_source": primary_source,  # Primary source for backward compatibility
            "sources": sources,  # List of all authoritative sources
            "notes": ing.get("notes", ""),
            # Evidence-backed risk attribution
            "evidence_reference_id": ing.get("evidence_reference_id"),
            "evidence_document_name": ing.get("evidence_document_name"),
            "evidence_strength": ing.get("evidence_strength"),
            "evidence_explanation": ing.get("evidence_explanation", "")
        })
    
    # Format low concern ingredients (Class 2: Known but low concern)
    low_concern_ingredients = []
    for item in analysis_result.get("low_concern_ingredients", []):
        if isinstance(item, dict):
            low_concern_ingredients.append({
                "name": item.get("name", "Unknown"),
                "risk_level": item.get("risk_level", "low"),
                "confidence": item.get("confidence", "high"),
                "notes": item.get("notes", ""),
                "sources": item.get("sources", [])
            })
    
    # Format beneficial ingredients (backward compatibility - uses low_concern_ingredients)
    beneficial_ingredients = []
    for item in analysis_result.get("low_concern_ingredients", []) or analysis_result.get("positive_ingredients", []):
        if isinstance(item, dict):
            beneficial_ingredients.append({
                "name": item.get("name", "Unknown"),
                "risk_level": item.get("risk_level", "low"),
                "confidence": item.get("confidence", "high"),
                "notes": item.get("notes", ""),
                "benefit": f"Low risk ingredient"
            })
        else:
            # Legacy format
            beneficial_ingredients.append({
                "name": item,
                "risk_level": "low",
                "confidence": "high",
                "notes": "",
                "benefit": f"Low risk ingredient"
            })
    
    # Format all ingredients for complete transparency
    all_ingredients_assessments = []
    for ing in analysis_result.get("all_ingredients", []):
        # Build reason
        reason_parts = []
        risk_level = ing.get("risk_level", "unknown")
        
        if ing.get("is_unknown") or risk_level == "unknown":
            reason_parts.append("Unknown ingredient - not found in safety database")
        else:
            reason_parts.append(f"{risk_level} risk level")
            if ing.get("explanation"):
                reason_parts.append(ing.get("explanation"))
        
        if ing.get("dosage_exceeded"):
            reason_parts.append("(concentration exceeds safe limit)")
        
        reason = ". ".join(reason_parts) if reason_parts else "Assessment completed"
        
        # Get sources
        sources = ing.get("sources", [])
        primary_source = ing.get("source")
        if primary_source and primary_source not in sources:
            sources.insert(0, primary_source)
        
        all_ingredients_assessments.append({
            "name": ing.get("name", ""),
            "risk_level": ing.get("risk_level", "unknown"),
            "confidence": ing.get("confidence", "unknown"),
            "reason": reason,
            "safe_dosage": ing.get("safe_limit"),
            "unit": ing.get("unit"),
            "exposure_context": f"Used in {product.category.value} products",
            "evidence_source": primary_source,
            "sources": sources,
            "notes": ing.get("notes", ""),
            "is_unknown": ing.get("is_unknown", False),
            # Evidence-backed risk attribution
            "evidence_reference_id": ing.get("evidence_reference_id"),
            "evidence_document_name": ing.get("evidence_document_name"),
            "evidence_strength": ing.get("evidence_strength"),
            "evidence_explanation": ing.get("evidence_explanation", "")
        })
    
    # Format unknown ingredients (Class 3: Unknown/insufficient data)
    unknown_ingredients_formatted = []
    for ing in analysis_result.get("unknown_ingredients", []):
        reason_parts = ["Insufficient data - not found in safety knowledge base"]
        reason = ". ".join(reason_parts)
        
        sources = ing.get("sources", [])
        primary_source = ing.get("source")
        if primary_source and primary_source not in sources:
            sources.insert(0, primary_source)
        
        unknown_ingredients_formatted.append({
            "name": ing.get("name", ""),
            "risk_level": "unknown",
            "confidence": "low",  # Always low for unknowns
            "reason": reason,
            "safe_dosage": None,
            "unit": None,
            "exposure_context": f"Used in {product.category.value} products",
            "evidence_source": None,
            "sources": [],
            "notes": ing.get("notes", "Insufficient public safety data available for this ingredient."),
            # Evidence-backed risk attribution (not available for unknown ingredients)
            "evidence_reference_id": None,
            "evidence_document_name": None,
            "evidence_strength": None,
            "evidence_explanation": ""
        })
    
    # Generate product-level summary using Product Summary Engine
    summary_engine = ProductSummaryEngine()
    product_summary = summary_engine.generate_summary(
        analysis_result=analysis_result,
        product_category=product.category.value if product.category else "general"
    )
    
    # Calculate unresolved ingredient statistics
    unresolved_count = len(unknown_ingredients_formatted)
    total_ingredients = len(all_ingredients_assessments)
    unresolved_ratio = unresolved_count / total_ingredients if total_ingredients > 0 else 0.0
    
    # Generate unresolved ingredient explanation
    unresolved_explanation = ""
    if unresolved_count > 0:
        if unresolved_count == 1:
            unresolved_explanation = (
                f"1 ingredient ({unresolved_count}/{total_ingredients}, {int(unresolved_ratio * 100)}%) "
                "could not be assessed because it was not found in our safety knowledge base. "
                "This does not mean the ingredient is unsafe - it simply means we don't have sufficient "
                "safety data available for it. Unresolved ingredients do not affect the safety score, "
                "but they do reduce our confidence in the overall assessment."
            )
        else:
            unresolved_explanation = (
                f"{unresolved_count} ingredients ({unresolved_count}/{total_ingredients}, {int(unresolved_ratio * 100)}%) "
                "could not be assessed because they were not found in our safety knowledge base. "
                "This does not mean these ingredients are unsafe - it simply means we don't have sufficient "
                "safety data available for them. Unresolved ingredients do not affect the safety score, "
                "but they do reduce our confidence in the overall assessment."
            )
    else:
        unresolved_explanation = (
            "All ingredients were successfully identified and assessed against our safety knowledge base. "
            "This provides high confidence in the safety assessment."
        )
    
    # Build explanation structure with three classes
    explanation = {
        "flagged_ingredients": flagged_ingredients,  # Class 1: Known & assessed (moderate/high risk)
        "low_concern_ingredients": low_concern_ingredients,  # Class 2: Known but low concern
        "unknown_ingredients": unknown_ingredients_formatted,  # Class 3: Unknown/insufficient data
        "beneficial_ingredients": beneficial_ingredients,  # Backward compatibility
        "all_ingredients": all_ingredients_assessments,  # Complete list of all ingredients
        "recommendation": analysis_result.get("recommendation", ""),
        "explanations": analysis_result.get("explanations", []),
        "ingredient_summary": analysis_result.get("ingredient_summary", {}),
        "overall_confidence": analysis_result.get("overall_confidence", "high"),
        # Product-level summary
        "product_summary": product_summary,
        # Unresolved ingredient information
        "unresolved_ingredient_count": unresolved_count,
        "total_ingredient_count": total_ingredients,
        "unresolved_ingredient_ratio": unresolved_ratio,
        "unresolved_ingredient_explanation": unresolved_explanation
    }
    
    # Build response with product ID, timestamp, and source attribution
    return {
        "product_id": product.id,
        "safety_score": analysis_result["safety_score"],
        "explanation": explanation,
        "computed_at": datetime.now().isoformat(),
        "product_source": product.source or "database"  # Include source attribution
    }


@router.post("/by-name", response_model=AnalysisResponse)
async def analyze_by_name(
    request: AnalyzeByNameRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze a product by name (and optionally brand/category).
    Used by web and mobile app.
    
    If product is not found locally:
    - Creates a new product record with provided information
    - Marks source as "manual"
    - Performs analysis (placeholder until full implementation)
    
    Future: Will fetch from external APIs when implemented.
    """
    # Find or create product
    product = _find_or_create_product(
        db=db,
        name=request.name,
        brand=request.brand,
        category=request.category
    )
    
    # Perform analysis
    analysis = _analyze_product(
        db=db,
        product=product,
        user_profile=request.user_profile
    )
    
    return analysis


def _analyze_ingredients(
    db: Session,
    ingredients_raw: str,
    product_name: Optional[str] = None,
    category: Optional[str] = None,
    user_profile: Optional[UserProfile] = None
) -> Dict[str, Any]:
    """
    Analyze a product from raw ingredient list without requiring a Product record.
    
    This function reuses the same normalization, matching, and safety engine pipeline
    as _analyze_product, but works directly with ingredient strings.
    
    Args:
        db: Database session
        ingredients_raw: Raw ingredient list (string, comma-separated or newline-separated)
        product_name: Optional product name for context
        category: Optional category (food/cosmetic/household/supplement)
        user_profile: Optional user profile for personalized analysis
        
    Returns:
        Analysis response dictionary with same structure as _analyze_product
    """
    # Convert user profile to dict if provided
    user_profile_dict = None
    if user_profile:
        user_profile_dict = {
            "sensitive_skin": user_profile.sensitive_skin,
            "pregnant": user_profile.pregnant,
            "child": user_profile.child
        }
    
    # Step 1: Check if ingredients are provided
    if not ingredients_raw or not ingredients_raw.strip():
        explanation = {
            "flagged_ingredients": [],
            "beneficial_ingredients": [],
            "recommendation": "No ingredients provided for analysis.",
            "explanations": [],
            "all_ingredients": [],
            "low_concern_ingredients": [],
            "unknown_ingredients": [],
            "ingredient_summary": {"total": 0},
            "overall_confidence": "low",
            "product_summary": {
                "verdict": "Context Dependent",
                "confidence": "low",
                "summary": "No ingredient information available for analysis.",
                "key_factors": ["No ingredients provided"]
            }
        }
        
        return {
            "product_id": None,  # No product ID for ingredient-only analysis
            "safety_score": 50,  # Neutral score when no data
            "explanation": explanation,
            "computed_at": datetime.now().isoformat(),
            "product_source": "manual"  # Manual ingredient input
        }
    
    # Step 2: Normalize and match ingredients using ingredient_normalizer
    # This is the same logic as _analyze_product
    matched_ingredients = normalize_and_match_ingredients(db, ingredients_raw)
    
    if not matched_ingredients:
        # Empty ingredient list after normalization
        explanation = {
            "flagged_ingredients": [],
            "beneficial_ingredients": [],
            "recommendation": "No valid ingredients found after normalization.",
            "explanations": [],
            "all_ingredients": [],
            "low_concern_ingredients": [],
            "unknown_ingredients": [],
            "ingredient_summary": {"total": 0},
            "overall_confidence": "low",
            "product_summary": {
                "verdict": "Context Dependent",
                "confidence": "low",
                "summary": "No valid ingredients could be extracted from the provided list.",
                "key_factors": ["Unable to parse ingredient list"]
            }
        }
        
        return {
            "product_id": None,
            "safety_score": 50,
            "explanation": explanation,
            "computed_at": datetime.now().isoformat(),
            "product_source": "manual"
        }
    
    # Step 3: Build ingredients_data structure (same as _analyze_product)
    # This code is identical to what's in _analyze_product - we'll reuse it
    ingredients_data = []
    
    for match_result in matched_ingredients:
        ingredient_id = match_result.get("ingredient_id")
        original_name = match_result.get("original_name", "")
        canonical_name = match_result.get("canonical_name")
        resolution_state = match_result.get("resolution_state", "unresolved")
        resolution_confidence = match_result.get("resolution_confidence", 0.0)
        match_explanation = match_result.get("match_explanation", "")
        
        if ingredient_id:
            # Look up ingredient in database
            ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
            
            if ingredient:
                # Get safety profiles for this ingredient
                safety_profiles = ingredient.ingredient_safety
                
                # Determine default exposure route based on category
                default_exposure = "skin"  # Default
                if category:
                    category_lower = category.lower()
                    if category_lower in ["food", "supplement"]:
                        default_exposure = "ingestion"
                    elif category_lower in ["household"]:
                        default_exposure = "inhalation"
                
                # Find matching safety profile or use defaults
                profile = None
                for sp in safety_profiles:
                    if sp.exposure_route.value == default_exposure:
                        profile = sp
                        break
                
                # If no matching profile, use first available or defaults
                if not profile and safety_profiles:
                    profile = safety_profiles[0]
                
                # Extract safety data
                risk_level = profile.risk_level.value if profile else "low"
                confidence = ingredient.confidence.value if ingredient.confidence else "medium"
                stored_notes = ingredient.notes or (profile.summary if profile else None)
                sources_list = ingredient.sources if isinstance(ingredient.sources, list) else []
                
                # Extract evidence fields from profile
                evidence_source = profile.source if profile else None
                evidence_reference_id = profile.reference_id if profile else None
                evidence_document_name = profile.document_name if profile else None
                evidence_strength = profile.evidence_strength.value if (profile and profile.evidence_strength) else None
                
                ingredients_data.append({
                    "name": canonical_name or ingredient.name,
                    "ingredient_id": ingredient_id,
                    "risk_level": risk_level,
                    "confidence": confidence,
                    "exposure_route": profile.exposure_route.value if profile else default_exposure,
                    "safe_limit": profile.safe_limit if profile else None,
                    "unit": profile.unit if profile else None,
                    "estimated_concentration": None,
                    "population_risk": profile.population_risk.value if profile else "general",
                    "summary": stored_notes or "Ingredient found in knowledge base but no detailed safety profile available",
                    "source": evidence_source,
                    "sources": sources_list,
                    "notes": stored_notes,
                    "is_unknown": False,
                    "match_type": match_result.get("match_type"),
                    "resolution_state": resolution_state,
                    "resolution_confidence": resolution_confidence,
                    "match_explanation": match_explanation,
                    "evidence_source": evidence_source,
                    "evidence_reference_id": evidence_reference_id,
                    "evidence_document_name": evidence_document_name,
                    "evidence_strength": evidence_strength
                })
            else:
                # Ingredient ID found but ingredient doesn't exist
                ingredients_data.append({
                    "name": original_name or canonical_name or "Unknown",
                    "ingredient_id": None,
                    "risk_level": "unknown",
                    "confidence": "unknown",
                    "exposure_route": "skin",
                    "safe_limit": None,
                    "unit": None,
                    "estimated_concentration": None,
                    "population_risk": "general",
                    "summary": "Ingredient ID found but ingredient record missing.",
                    "source": None,
                    "sources": [],
                    "notes": "Ingredient not found in knowledge base. Safety data unavailable.",
                    "is_unknown": True,
                    "match_type": None,
                    "resolution_state": "unresolved",
                    "resolution_confidence": 0.0,
                    "match_explanation": match_explanation or f"'{original_name}' was not found in the safety knowledge base."
                })
        else:
            # Ingredient not found in knowledge base
            ingredients_data.append({
                "name": original_name or "Unknown",
                "ingredient_id": None,
                "risk_level": "unknown",
                "confidence": "unknown",
                "exposure_route": "skin",
                "safe_limit": None,
                "unit": None,
                "estimated_concentration": None,
                "population_risk": "general",
                "summary": "Ingredient not found in safety knowledge base. Assessment based on limited information.",
                "source": None,
                "sources": [],
                "notes": "Ingredient not found in knowledge base. Safety data unavailable.",
                "is_unknown": True,
                "match_type": None,
                "resolution_state": "unresolved",
                "resolution_confidence": 0.0,
                "match_explanation": match_explanation or f"'{original_name}' was not found in the safety knowledge base."
            })
    
    # Step 4: Pass structured ingredient data into SafetyEngine (same as _analyze_product)
    safety_engine = SafetyEngine()
    analysis_result = safety_engine.analyze(
        ingredients=ingredients_data,
        user_profile=user_profile_dict
    )
    
    # Step 5: Format response (reuse the same formatting logic from _analyze_product)
    # This is a large block - let me extract the key parts
    flagged_ingredients = []
    for ing in analysis_result.get("flagged_ingredients", []):
        reason_parts = []
        risk_level = ing.get("risk_level", "unknown")
        
        if ing.get("is_unknown") or risk_level == "unknown":
            reason_parts.append("Unknown ingredient - not found in safety database")
        else:
            reason_parts.append(f"{risk_level} risk level")
            if ing.get("explanation"):
                reason_parts.append(ing.get("explanation"))
        
        if ing.get("dosage_exceeded"):
            reason_parts.append("(concentration exceeds safe limit)")
        
        reason = ". ".join(reason_parts) if reason_parts else "Safety concern identified"
        
        sources = ing.get("sources", [])
        primary_source = ing.get("source")
        if primary_source and primary_source not in sources:
            sources.insert(0, primary_source)
        
        # Extract evidence fields
        evidence_source = ing.get("evidence_source")
        evidence_reference_id = ing.get("evidence_reference_id")
        evidence_document_name = ing.get("evidence_document_name")
        evidence_strength = ing.get("evidence_strength")
        
        # Generate evidence explanation
        evidence_explanation = ""
        if evidence_source or evidence_reference_id:
            evidence_parts = []
            if evidence_source:
                evidence_parts.append(f"Source: {evidence_source}")
            if evidence_document_name:
                evidence_parts.append(f"Document: {evidence_document_name}")
            if evidence_reference_id:
                evidence_parts.append(f"Reference: {evidence_reference_id}")
            if evidence_strength:
                evidence_parts.append(f"Evidence strength: {evidence_strength}")
            evidence_explanation = ". ".join(evidence_parts)
        
        # Combine notes with evidence explanation
        notes = ing.get("notes", "")
        if evidence_explanation:
            notes = f"{notes}. {evidence_explanation}" if notes else evidence_explanation
        
        flagged_ingredients.append({
            "name": ing.get("name", ""),
            "risk_level": risk_level,
            "confidence": ing.get("confidence", "unknown"),
            "reason": reason,
            "safe_dosage": ing.get("safe_limit"),
            "unit": ing.get("unit"),
            "exposure_context": f"Used in {category or 'general'} products" if category else "General use",
            "evidence_source": evidence_source,
            "sources": sources,
            "notes": notes,
            "evidence_reference_id": evidence_reference_id,
            "evidence_document_name": evidence_document_name,
            "evidence_strength": evidence_strength,
            "evidence_explanation": evidence_explanation
        })
    
    # Format beneficial ingredients
    beneficial_ingredients = []
    for ing in analysis_result.get("beneficial_ingredients", []):
        if isinstance(ing, str):
            beneficial_ingredients.append({
                "name": ing,
                "benefit": f"Contains {ing}, which may provide health benefits"
            })
        else:
            beneficial_ingredients.append({
                "name": ing.get("name", ""),
                "benefit": ing.get("benefit", f"Contains {ing.get('name', '')}, which may provide health benefits")
            })
    
    # Format low concern ingredients
    low_concern_ingredients = []
    for ing in analysis_result.get("low_concern_ingredients", []):
        low_concern_ingredients.append({
            "name": ing.get("name", ""),
            "risk_level": ing.get("risk_level", "low"),
            "confidence": ing.get("confidence", "high"),
            "notes": ing.get("notes", "Generally recognized as safe")
        })
    
    # Format unknown ingredients
    unknown_ingredients_formatted = []
    for ing in analysis_result.get("unknown_ingredients", []):
        reason = f"'{ing.get('name', 'Unknown')}' was not found in the safety knowledge base. Assessment cannot be completed without additional data."
        
        unknown_ingredients_formatted.append({
            "name": ing.get("name", ""),
            "risk_level": "unknown",
            "confidence": "low",
            "reason": reason,
            "safe_dosage": None,
            "unit": None,
            "exposure_context": f"Used in {category or 'general'} products" if category else "General use",
            "evidence_source": None,
            "sources": [],
            "notes": ing.get("notes", "Insufficient public safety data available for this ingredient."),
            "evidence_reference_id": None,
            "evidence_document_name": None,
            "evidence_strength": None,
            "evidence_explanation": ""
        })
    
    # Format all ingredients assessments
    all_ingredients_assessments = []
    for ing in analysis_result.get("all_ingredients", []):
        risk_level = ing.get("risk_level", "unknown")
        confidence = ing.get("confidence", "unknown")
        
        reason_parts = []
        if ing.get("is_unknown") or risk_level == "unknown":
            reason_parts.append("Unknown ingredient - not found in safety database")
        else:
            reason_parts.append(f"{risk_level} risk level")
            if ing.get("explanation"):
                reason_parts.append(ing.get("explanation"))
        
        reason = ". ".join(reason_parts) if reason_parts else "Assessment completed"
        
        sources = ing.get("sources", [])
        primary_source = ing.get("source")
        if primary_source and primary_source not in sources:
            sources.insert(0, primary_source)
        
        # Extract evidence fields
        evidence_source = ing.get("evidence_source")
        evidence_reference_id = ing.get("evidence_reference_id")
        evidence_document_name = ing.get("evidence_document_name")
        evidence_strength = ing.get("evidence_strength")
        
        # Generate evidence explanation
        evidence_explanation = ""
        if evidence_source or evidence_reference_id:
            evidence_parts = []
            if evidence_source:
                evidence_parts.append(f"Source: {evidence_source}")
            if evidence_document_name:
                evidence_parts.append(f"Document: {evidence_document_name}")
            if evidence_reference_id:
                evidence_parts.append(f"Reference: {evidence_reference_id}")
            if evidence_strength:
                evidence_parts.append(f"Evidence strength: {evidence_strength}")
            evidence_explanation = ". ".join(evidence_parts)
        
        # Combine notes with evidence explanation
        notes = ing.get("notes", "")
        if evidence_explanation:
            notes = f"{notes}. {evidence_explanation}" if notes else evidence_explanation
        
        all_ingredients_assessments.append({
            "name": ing.get("name", ""),
            "risk_level": risk_level,
            "confidence": confidence,
            "reason": reason,
            "safe_dosage": ing.get("safe_limit"),
            "unit": ing.get("unit"),
            "exposure_context": f"Used in {category or 'general'} products" if category else "General use",
            "evidence_source": evidence_source,
            "sources": sources,
            "notes": notes,
            "is_unknown": ing.get("is_unknown", False),
            "evidence_reference_id": evidence_reference_id,
            "evidence_document_name": evidence_document_name,
            "evidence_strength": evidence_strength,
            "evidence_explanation": evidence_explanation
        })
    
    # Generate product-level summary using Product Summary Engine
    summary_engine = ProductSummaryEngine()
    product_summary = summary_engine.generate_summary(
        analysis_result=analysis_result,
        product_category=category or "general"
    )
    
    # Calculate unresolved ingredient statistics
    unresolved_count = len(unknown_ingredients_formatted)
    total_ingredients = len(all_ingredients_assessments)
    unresolved_ratio = unresolved_count / total_ingredients if total_ingredients > 0 else 0.0
    
    # Generate unresolved ingredient explanation
    unresolved_explanation = ""
    if unresolved_count > 0:
        if unresolved_count == 1:
            unresolved_explanation = (
                f"1 ingredient ({unresolved_count}/{total_ingredients}, {int(unresolved_ratio * 100)}%) "
                "could not be assessed because it was not found in our safety knowledge base. "
                "This does not mean the ingredient is unsafe - it simply means we don't have sufficient "
                "safety data available for it. Unresolved ingredients do not affect the safety score, "
                "but they do reduce our confidence in the overall assessment."
            )
        else:
            unresolved_explanation = (
                f"{unresolved_count} ingredients ({unresolved_count}/{total_ingredients}, {int(unresolved_ratio * 100)}%) "
                "could not be assessed because they were not found in our safety knowledge base. "
                "This does not mean these ingredients are unsafe - it simply means we don't have sufficient "
                "safety data available for them. Unresolved ingredients do not affect the safety score, "
                "but they do reduce our confidence in the overall assessment."
            )
    else:
        unresolved_explanation = (
            "All ingredients were successfully identified and assessed against our safety knowledge base. "
            "This provides high confidence in the safety assessment."
        )
    
    # Build explanation structure
    explanation = {
        "flagged_ingredients": flagged_ingredients,
        "low_concern_ingredients": low_concern_ingredients,
        "unknown_ingredients": unknown_ingredients_formatted,
        "beneficial_ingredients": beneficial_ingredients,
        "all_ingredients": all_ingredients_assessments,
        "recommendation": analysis_result.get("recommendation", ""),
        "explanations": analysis_result.get("explanations", []),
        "ingredient_summary": analysis_result.get("ingredient_summary", {}),
        "overall_confidence": analysis_result.get("overall_confidence", "high"),
        "product_summary": product_summary,
        # Unresolved ingredient information
        "unresolved_ingredient_count": unresolved_count,
        "total_ingredient_count": total_ingredients,
        "unresolved_ingredient_ratio": unresolved_ratio,
        "unresolved_ingredient_explanation": unresolved_explanation
    }
    
    # Build response
    return {
        "product_id": None,  # No product ID for ingredient-only analysis
        "safety_score": analysis_result["safety_score"],
        "explanation": explanation,
        "computed_at": datetime.now().isoformat(),
        "product_source": "manual"  # Manual ingredient input
    }


@router.post("/by-ingredients", response_model=AnalysisResponse)
async def analyze_by_ingredients(
    request: AnalyzeByIngredientsRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze a product from a raw ingredient list without requiring barcode or product record.
    
    Accepts ingredients as:
    - String (comma-separated or newline-separated): "Water, Glycerin, Sodium Lauryl Sulfate"
    - Array: ["Water", "Glycerin", "Sodium Lauryl Sulfate"]
    
    Runs the same analysis pipeline as barcode-based products:
    - Normalizes and matches ingredients
    - Fetches safety data from knowledge base
    - Computes safety score
    - Generates product-level summary and verdict
    
    Does NOT depend on external APIs - works entirely with local knowledge base.
    
    Returns the same analysis response structure as /analyze/product.
    """
    try:
        # Convert ingredients to string format if array is provided
        if isinstance(request.ingredients, list):
            # Join array elements with commas
            ingredients_raw = ", ".join(str(ing) for ing in request.ingredients if ing)
        else:
            # Already a string
            ingredients_raw = request.ingredients
        
        # Determine category enum if provided
        category_enum = None
        if request.category:
            category_lower = request.category.lower()
            try:
                category_enum = Category[category_lower.upper()]
            except (KeyError, AttributeError):
                # Invalid category, will use None (defaults to "general" in analysis)
                logger.warning(f"Invalid category provided: {request.category}")
        
        # Perform analysis
        analysis = _analyze_ingredients(
            db=db,
            ingredients_raw=ingredients_raw,
            product_name=request.product_name,
            category=request.category,  # Pass as string, will be used in exposure context
            user_profile=request.user_profile
        )
        
        # Persist product to database if product name is provided
        # This allows text search to find it later
        if request.product_name and ingredients_raw:
            try:
                # Check if product already exists
                existing_product = None
                if request.product_name:
                    existing_product = db.query(Product).filter(
                        Product.name.ilike(request.product_name.strip())
                    ).first()
                
                if not existing_product:
                    # Create new product record
                    new_product = Product(
                        name=request.product_name.strip(),
                        brand=None,  # Not provided in ingredient-only analysis
                        category=category_enum or Category.FOOD,  # Default to FOOD if not specified
                        ingredients_raw=ingredients_raw,
                        source="manual",  # Mark as manually entered
                        last_fetched=datetime.utcnow()
                    )
                    db.add(new_product)
                    db.commit()
                    db.refresh(new_product)
                    
                    # Update analysis response with product ID
                    analysis["product_id"] = new_product.id
                    logger.info(f"Saved product to database: id={new_product.id}, name={new_product.name}")
                else:
                    # Update existing product with ingredients if missing
                    if not existing_product.ingredients_raw:
                        existing_product.ingredients_raw = ingredients_raw
                        existing_product.last_fetched = datetime.utcnow()
                        db.commit()
                    
                    # Update analysis response with product ID
                    analysis["product_id"] = existing_product.id
                    logger.info(f"Updated existing product: id={existing_product.id}, name={existing_product.name}")
            except Exception as e:
                logger.warning(f"Failed to persist product to database: {e}", exc_info=True)
                # Don't fail the analysis if persistence fails
                db.rollback()
        
        # Ensure response has correct structure
        if not isinstance(analysis, dict):
            raise ValueError("Analysis function returned invalid format")
        
        if "explanation" not in analysis:
            analysis["explanation"] = {
                "flagged_ingredients": [],
                "beneficial_ingredients": [],
                "recommendation": "Analysis completed",
                "explanations": []
            }
        
        return analysis
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing ingredients: {str(e)}"
        )


@router.get("/ingredient/{name}", response_model=IngredientSafetyResponse)
async def get_ingredient_safety(
    name: str,
    db: Session = Depends(get_db)
):
    """
    Get ingredient safety profile.
    Returns safety information for a specific ingredient.
    """
    ingredient = db.query(Ingredient).filter(Ingredient.name.ilike(f"%{name}%")).first()
    
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    
    # Get all safety profiles for this ingredient
    safety_profiles = ingredient.ingredient_safety
    
    return {
        "ingredient_id": ingredient.id,
        "name": ingredient.name,
        "inci_name": ingredient.inci_name,
        "cas_number": ingredient.cas_number,
        "category": ingredient.category,
        "evidence_strength": ingredient.evidence_strength,
        "notes": ingredient.notes,
        "safety_profiles": [
            {
                "exposure_route": profile.exposure_route,
                "safe_limit": profile.safe_limit,
                "unit": profile.unit,
                "risk_level": profile.risk_level,
                "population_risk": profile.population_risk,
                "summary": profile.summary,
                "source": profile.source
            }
            for profile in safety_profiles
        ]
    }
