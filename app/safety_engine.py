"""Safety scoring engine for product analysis."""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.models import (
    Product, ProductIngredient, Ingredient, IngredientSafety, ProductScore,
    RiskLevel, ExposureRoute, PopulationRisk, Category
)


class SafetyEngine:
    """Engine for computing product safety scores with explainable output."""
    
    # Risk level deduction points
    RISK_DEDUCTIONS = {
        RiskLevel.LOW: 2,
        RiskLevel.MODERATE: 10,
        RiskLevel.HIGH: 25
    }
    
    # User profile adjustment multipliers
    PROFILE_ADJUSTMENTS = {
        "sensitive_skin": 0.9,  # 10% reduction for sensitive skin
        "pregnant": 0.85,      # 15% reduction for pregnancy
        "child": 0.8           # 20% reduction for children
    }
    
    # Exposure route mapping for product categories
    CATEGORY_EXPOSURE_ROUTES = {
        Category.FOOD: [ExposureRoute.INGESTION],
        Category.COSMETIC: [ExposureRoute.SKIN, ExposureRoute.INHALATION],
        Category.HOUSEHOLD: [ExposureRoute.SKIN, ExposureRoute.INHALATION, ExposureRoute.INGESTION],
        Category.SUPPLEMENT: [ExposureRoute.INGESTION]
    }
    
    @classmethod
    def _get_relevant_exposure_routes(cls, product_category: Category) -> List[ExposureRoute]:
        """Get relevant exposure routes for a product category."""
        return cls.CATEGORY_EXPOSURE_ROUTES.get(product_category, [ExposureRoute.SKIN])
    
    @classmethod
    def _calculate_ingredient_penalty(
        cls,
        safety_profile: IngredientSafety,
        concentration: Optional[float] = None,
        exposure_route: ExposureRoute = None
    ) -> Tuple[int, str]:
        """
        Calculate penalty points for an ingredient based on safety profile.
        
        Returns:
            Tuple of (penalty_points, reason_string)
        """
        base_penalty = cls.RISK_DEDUCTIONS.get(safety_profile.risk_level, 0)
        
        # Adjust penalty based on concentration if available
        penalty = base_penalty
        reason_parts = []
        
        if safety_profile.safe_limit and concentration:
            # If concentration exceeds safe limit, increase penalty
            if concentration > safety_profile.safe_limit:
                excess_ratio = concentration / safety_profile.safe_limit
                if excess_ratio > 2.0:
                    penalty = int(base_penalty * 1.5)  # 50% increase for >2x limit
                    reason_parts.append(f"concentration ({concentration} {safety_profile.unit or ''}) exceeds safe limit by {excess_ratio:.1f}x")
                elif excess_ratio > 1.5:
                    penalty = int(base_penalty * 1.25)  # 25% increase for >1.5x limit
                    reason_parts.append(f"concentration ({concentration} {safety_profile.unit or ''}) exceeds safe limit by {excess_ratio:.1f}x")
            else:
                # Within safe limits, reduce penalty
                penalty = max(1, int(base_penalty * 0.5))
                reason_parts.append(f"within safe limits ({concentration} {safety_profile.unit or ''} vs {safety_profile.safe_limit} {safety_profile.unit or ''})")
        
        # Build reason string
        risk_desc = safety_profile.risk_level.value
        if safety_profile.summary:
            reason_parts.append(safety_profile.summary)
        elif not reason_parts:
            reason_parts.append(f"{risk_desc} risk level")
        
        reason = ". ".join(reason_parts) if reason_parts else f"{risk_desc} risk"
        
        return penalty, reason
    
    @classmethod
    def _is_beneficial_ingredient(cls, ingredient: Ingredient) -> bool:
        """
        Determine if an ingredient is considered beneficial.
        
        This is a placeholder - in a full implementation, this would check
        against a database of beneficial ingredients or use ML classification.
        """
        # Common beneficial ingredients (simplified check)
        beneficial_keywords = [
            "vitamin", "antioxidant", "omega", "probiotic", "fiber",
            "mineral", "calcium", "iron", "zinc", "magnesium"
        ]
        
        name_lower = ingredient.name.lower()
        return any(keyword in name_lower for keyword in beneficial_keywords)
    
    @classmethod
    def compute_safety_score(
        cls,
        db: Session,
        product: Product,
        user_profile: Optional[Dict[str, bool]] = None
    ) -> Dict[str, Any]:
        """
        Compute safety score for a product with explainable output.
        
        Args:
            db: Database session
            product: Product to analyze
            user_profile: Optional dict with keys: sensitive_skin, pregnant, child
        
        Returns:
            Dictionary with safety_score, explanation, and detailed breakdown
        """
        # Start with base score of 100
        base_score = 100
        total_penalty = 0
        
        flagged_ingredients = []
        beneficial_ingredients = []
        
        # Get relevant exposure routes for this product category
        relevant_routes = cls._get_relevant_exposure_routes(product.category)
        
        # Analyze each ingredient in the product
        if not product.product_ingredients or len(product.product_ingredients) == 0:
            # No ingredients to analyze
            return {
                "safety_score": 50,  # Neutral score when no data
                "explanation": {
                    "flagged_ingredients": [],
                    "beneficial_ingredients": [],
                    "recommendation": (
                        "Product information is limited. "
                        "Ingredient analysis not yet available. "
                        "External API integration pending."
                    ),
                    "score_breakdown": {
                        "base_score": 100,
                        "total_penalty": 0,
                        "final_score": 50,
                        "reason": "No ingredient data available"
                    }
                }
            }
        
        # Process each product ingredient
        for product_ingredient in product.product_ingredients:
            ingredient = product_ingredient.ingredient
            concentration = product_ingredient.estimated_concentration
            
            # Check if ingredient is beneficial
            if cls._is_beneficial_ingredient(ingredient):
                beneficial_ingredients.append({
                    "name": ingredient.name,
                    "benefit": f"Contains {ingredient.name}, which may provide health benefits"
                })
            
            # Get safety profiles for this ingredient
            safety_profiles = ingredient.ingredient_safety
            
            if not safety_profiles:
                # No safety data available - small penalty for uncertainty
                total_penalty += 1
                flagged_ingredients.append({
                    "name": ingredient.name,
                    "reason": "No safety data available for this ingredient",
                    "safe_dosage": None,
                    "unit": None,
                    "exposure_context": f"Used in {product.category.value} products",
                    "evidence_source": None
                })
                continue
            
            # Find relevant safety profiles based on exposure route
            # Prioritize profiles that match user profile and exposure route
            relevant_profiles = []
            
            for safety_profile in safety_profiles:
                # Check if this exposure route is relevant for the product
                if safety_profile.exposure_route not in relevant_routes:
                    continue
                
                # Check population risk matching
                is_relevant = False
                priority = 0  # Higher priority = more relevant
                
                if safety_profile.population_risk == PopulationRisk.GENERAL:
                    # General population is always relevant
                    is_relevant = True
                    priority = 1
                elif user_profile:
                    # Check if profile matches user's specific needs
                    if user_profile.get("sensitive_skin") and safety_profile.population_risk == PopulationRisk.SENSITIVE_SKIN:
                        is_relevant = True
                        priority = 3  # High priority for specific match
                    elif user_profile.get("pregnant") and safety_profile.population_risk == PopulationRisk.PREGNANCY:
                        is_relevant = True
                        priority = 3
                    elif user_profile.get("child") and safety_profile.population_risk == PopulationRisk.CHILDREN:
                        is_relevant = True
                        priority = 3
                    else:
                        # Specific population risk but doesn't match user profile
                        # Still include but with lower priority
                        is_relevant = True
                        priority = 2
                else:
                    # No user profile, include all population-specific profiles
                    is_relevant = True
                    priority = 2
                
                if is_relevant:
                    relevant_profiles.append((safety_profile, priority))
            
            # Sort by priority (highest first) and process the most relevant profile
            if relevant_profiles:
                relevant_profiles.sort(key=lambda x: x[1], reverse=True)
                safety_profile, _ = relevant_profiles[0]
                
                # Calculate penalty for this ingredient
                penalty, reason = cls._calculate_ingredient_penalty(
                    safety_profile,
                    concentration,
                    safety_profile.exposure_route
                )
                
                total_penalty += penalty
                
                # Build flagged ingredient entry
                flagged_ingredients.append({
                    "name": ingredient.name,
                    "reason": reason,
                    "safe_dosage": safety_profile.safe_limit,
                    "unit": safety_profile.unit,
                    "exposure_context": f"{safety_profile.exposure_route.value} exposure in {product.category.value} products",
                    "evidence_source": safety_profile.source
                })
        
        # Calculate final score
        final_score = max(0, min(100, base_score - total_penalty))
        
        # Apply user profile adjustments
        if user_profile:
            adjustment_factor = 1.0
            adjustment_reasons = []
            
            if user_profile.get("sensitive_skin"):
                adjustment_factor *= cls.PROFILE_ADJUSTMENTS["sensitive_skin"]
                adjustment_reasons.append("sensitive skin")
            if user_profile.get("pregnant"):
                adjustment_factor *= cls.PROFILE_ADJUSTMENTS["pregnant"]
                adjustment_reasons.append("pregnancy")
            if user_profile.get("child"):
                adjustment_factor *= cls.PROFILE_ADJUSTMENTS["child"]
                adjustment_reasons.append("children")
            
            if adjustment_reasons:
                adjusted_score = int(final_score * adjustment_factor)
                final_score = max(0, min(100, adjusted_score))
        
        # Generate recommendation
        recommendation = cls._generate_recommendation(
            final_score,
            flagged_ingredients,
            beneficial_ingredients,
            user_profile
        )
        
        # Build explanation
        explanation = {
            "flagged_ingredients": flagged_ingredients,
            "beneficial_ingredients": beneficial_ingredients,
            "recommendation": recommendation,
            "score_breakdown": {
                "base_score": base_score,
                "total_penalty": total_penalty,
                "final_score": final_score,
                "ingredients_analyzed": len(product.product_ingredients),
                "flagged_count": len(flagged_ingredients),
                "beneficial_count": len(beneficial_ingredients)
            }
        }
        
        return {
            "safety_score": final_score,
            "explanation": explanation
        }
    
    @classmethod
    def _generate_recommendation(
        cls,
        score: int,
        flagged_ingredients: List[Dict[str, Any]],
        beneficial_ingredients: List[Dict[str, Any]],
        user_profile: Optional[Dict[str, bool]] = None
    ) -> str:
        """Generate human-readable recommendation based on score and analysis."""
        recommendation_parts = []
        
        # Score-based recommendation
        if score >= 80:
            recommendation_parts.append("This product has a good safety profile.")
        elif score >= 60:
            recommendation_parts.append("This product has a moderate safety profile with some concerns.")
        elif score >= 40:
            recommendation_parts.append("This product has notable safety concerns.")
        else:
            recommendation_parts.append("This product has significant safety concerns.")
        
        # Ingredient-specific recommendations
        if flagged_ingredients:
            high_risk_count = sum(
                1 for ing in flagged_ingredients
                if "high risk" in ing.get("reason", "").lower()
            )
            
            if high_risk_count > 0:
                recommendation_parts.append(
                    f"{high_risk_count} ingredient(s) with high risk levels were identified. "
                    "Review the flagged ingredients for details."
                )
            else:
                recommendation_parts.append(
                    f"{len(flagged_ingredients)} ingredient(s) require attention. "
                    "Check safe dosage limits and exposure contexts."
                )
        
        if beneficial_ingredients:
            recommendation_parts.append(
                f"The product contains {len(beneficial_ingredients)} potentially beneficial ingredient(s)."
            )
        
        # User profile specific notes
        if user_profile:
            profile_notes = []
            if user_profile.get("sensitive_skin"):
                profile_notes.append("Consider patch testing due to sensitive skin")
            if user_profile.get("pregnant"):
                profile_notes.append("Consult healthcare provider during pregnancy")
            if user_profile.get("child"):
                profile_notes.append("Use age-appropriate formulations for children")
            
            if profile_notes:
                recommendation_parts.append(" ".join(profile_notes) + ".")
        
        # Evidence-based note
        if flagged_ingredients:
            sources = set(
                ing.get("evidence_source")
                for ing in flagged_ingredients
                if ing.get("evidence_source")
            )
            if sources:
                recommendation_parts.append(
                    f"Safety assessments are based on evidence from: {', '.join(sorted(sources))}."
                )
        
        return " ".join(recommendation_parts)
    
    @classmethod
    def save_score_to_db(
        cls,
        db: Session,
        product: Product,
        analysis_result: Dict[str, Any],
        user_profile: Optional[Dict[str, bool]] = None
    ) -> Optional[ProductScore]:
        """
        Optionally save computed score to database.
        
        Only saves general population scores (not user-specific ones)
        to avoid storing personalized scores as canonical.
        
        Args:
            db: Database session
            product: Product that was analyzed
            analysis_result: Result from compute_safety_score
            user_profile: User profile used (if any)
        
        Returns:
            ProductScore if saved, None otherwise
        """
        # Only save general population scores (no user profile)
        if user_profile and any(user_profile.values()):
            return None
        
        # Create or update product score
        product_score = db.query(ProductScore).filter(
            ProductScore.product_id == product.id
        ).first()
        
        if product_score:
            # Update existing score
            product_score.safety_score = analysis_result["safety_score"]
            product_score.explanation = analysis_result["explanation"]
        else:
            # Create new score
            product_score = ProductScore(
                product_id=product.id,
                safety_score=analysis_result["safety_score"],
                explanation=analysis_result["explanation"]
            )
            db.add(product_score)
        
        db.commit()
        db.refresh(product_score)
        
        return product_score
