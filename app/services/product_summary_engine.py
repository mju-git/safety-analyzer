"""Product Summary Engine - Aggregates ingredient analysis into product-level summary and verdict."""
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ProductSummaryEngine:
    """
    Generates product-level summaries and verdicts from ingredient analysis.
    
    Produces:
    - Verdict (Generally Safe, Context Dependent, Use With Caution)
    - Confidence level (High/Medium/Low)
    - Layman-friendly summary (1-3 sentences)
    - Key contributing factors (up to 3)
    """
    
    # Verdict thresholds based on safety score
    VERDICT_THRESHOLDS = {
        "Generally Safe": (70, 100),  # Score 70-100
        "Context Dependent": (40, 69),  # Score 40-69
        "Use With Caution": (0, 39)  # Score 0-39
    }
    
    def generate_summary(
        self,
        analysis_result: Dict[str, Any],
        product_category: str = "general"
    ) -> Dict[str, Any]:
        """
        Generate product-level summary from ingredient analysis.
        
        Args:
            analysis_result: Result from SafetyEngine.analyze()
            product_category: Product category (food/cosmetic/household/supplement)
            
        Returns:
            Dict with:
                - verdict: "Generally Safe" | "Context Dependent" | "Use With Caution"
                - confidence: "high" | "medium" | "low"
                - summary: Short layman-friendly summary (1-3 sentences)
                - key_factors: List of up to 3 key contributing factors
        """
        safety_score = analysis_result.get("safety_score", 50)
        flagged_ingredients = analysis_result.get("flagged_ingredients", [])
        unknown_ingredients = analysis_result.get("unknown_ingredients", [])
        low_concern_ingredients = analysis_result.get("low_concern_ingredients", [])
        all_ingredients = analysis_result.get("all_ingredients", [])
        overall_confidence = analysis_result.get("overall_confidence", "high")
        ingredient_summary = analysis_result.get("ingredient_summary", {})
        
        # Determine verdict based on safety score
        verdict = self._determine_verdict(safety_score)
        
        # Calculate comprehensive confidence
        confidence = self._calculate_comprehensive_confidence(
            overall_confidence,
            all_ingredients,
            flagged_ingredients,
            unknown_ingredients
        )
        
        # Generate layman-friendly summary
        summary = self._generate_layman_summary(
            verdict,
            safety_score,
            flagged_ingredients,
            unknown_ingredients,
            low_concern_ingredients,
            ingredient_summary,
            product_category
        )
        
        # Identify key contributing factors
        key_factors = self._identify_key_factors(
            flagged_ingredients,
            unknown_ingredients,
            ingredient_summary,
            safety_score
        )
        
        return {
            "verdict": verdict,
            "confidence": confidence,
            "summary": summary,
            "key_factors": key_factors
        }
    
    def _determine_verdict(self, safety_score: int) -> str:
        """
        Determine verdict based on safety score.
        
        Args:
            safety_score: Safety score (0-100)
            
        Returns:
            Verdict string
        """
        if safety_score >= 70:
            return "Generally Safe"
        elif safety_score >= 40:
            return "Context Dependent"
        else:
            return "Use With Caution"
    
    def _calculate_comprehensive_confidence(
        self,
        overall_confidence: str,
        all_ingredients: List[Dict[str, Any]],
        flagged_ingredients: List[Dict[str, Any]],
        unknown_ingredients: List[Dict[str, Any]]
    ) -> str:
        """
        Calculate comprehensive confidence based on ingredient resolution coverage.
        
        Confidence is based on:
        1. Resolution coverage: What percentage of ingredients were successfully resolved?
        2. Resolution quality: How confident are we in the matches (resolved vs resolved_inferred)?
        3. Evidence strength: How strong is the evidence for flagged ingredients?
        
        Safety score and confidence are separate concepts:
        - Safety score: Based on known risks of resolved ingredients
        - Confidence: Based on data quality and coverage
        
        Args:
            overall_confidence: Overall confidence from safety engine
            all_ingredients: All ingredient assessments
            flagged_ingredients: Flagged ingredients
            unknown_ingredients: Unknown ingredients
            
        Returns:
            Confidence level: "high", "medium", or "low"
        """
        if not all_ingredients:
            return "low"
        
        total_ingredients = len(all_ingredients)
        unresolved_count = len(unknown_ingredients)
        resolved_count = sum(1 for ing in all_ingredients if ing.get("resolution_state") == "resolved")
        inferred_count = sum(1 for ing in all_ingredients if ing.get("resolution_state") == "resolved_inferred")
        
        # Factor 1: Resolution coverage (most important)
        # What percentage of ingredients were successfully resolved?
        resolution_coverage = (resolved_count + inferred_count) / total_ingredients if total_ingredients > 0 else 0.0
        unresolved_ratio = unresolved_count / total_ingredients if total_ingredients > 0 else 1.0
        
        # Factor 2: Resolution quality
        # Prefer fully resolved over inferred matches
        if resolved_count + inferred_count > 0:
            resolution_quality = resolved_count / (resolved_count + inferred_count)
        else:
            resolution_quality = 0.0
        
        # Factor 3: Average resolution confidence for resolved ingredients
        resolved_ingredients = [ing for ing in all_ingredients if ing.get("resolution_state") != "unresolved"]
        if resolved_ingredients:
            avg_resolution_confidence = sum(
                ing.get("resolution_confidence", 0.0) for ing in resolved_ingredients
            ) / len(resolved_ingredients)
        else:
            avg_resolution_confidence = 0.0
        
        # Factor 4: Evidence strength of flagged ingredients (only if we have flagged ingredients)
        evidence_scores = []
        for ing in flagged_ingredients:
            evidence_strength = ing.get("evidence_strength")
            if evidence_strength:
                strength_str = evidence_strength.lower() if isinstance(evidence_strength, str) else str(evidence_strength).lower()
                if strength_str == "high":
                    evidence_scores.append(1.0)
                elif strength_str == "medium":
                    evidence_scores.append(0.7)
                elif strength_str == "low":
                    evidence_scores.append(0.4)
                else:
                    evidence_scores.append(0.2)
            else:
                evidence_scores.append(0.2)
        
        avg_evidence_strength = sum(evidence_scores) / len(evidence_scores) if evidence_scores else 0.5
        
        # Calculate composite confidence score
        # Resolution coverage is most important (50% weight)
        # Resolution quality and confidence (30% weight)
        # Evidence strength (20% weight, only if we have flagged ingredients)
        
        confidence_score = 0.0
        
        # Resolution coverage component (0-1, higher is better)
        confidence_score += resolution_coverage * 0.5
        
        # Resolution quality and confidence component (0-1, higher is better)
        quality_confidence_component = (resolution_quality * 0.5) + (avg_resolution_confidence * 0.5)
        confidence_score += quality_confidence_component * 0.3
        
        # Evidence strength component (0-1, higher is better)
        # Only apply if we have flagged ingredients, otherwise use neutral score
        if flagged_ingredients:
            confidence_score += avg_evidence_strength * 0.2
        else:
            confidence_score += 0.5 * 0.2  # Neutral if no flagged ingredients
        
        # Determine confidence level with clear thresholds
        # High: >80% resolved, >70% fully resolved (not inferred), strong evidence
        # Medium: 50-80% resolved, or mixed resolution quality
        # Low: <50% resolved, or many unresolved/inferred
        
        if resolution_coverage >= 0.8 and resolution_quality >= 0.7 and unresolved_ratio < 0.2:
            return "high"
        elif resolution_coverage >= 0.5 and unresolved_ratio < 0.5:
            return "medium"
        else:
            return "low"
    
    def _generate_layman_summary(
        self,
        verdict: str,
        safety_score: int,
        flagged_ingredients: List[Dict[str, Any]],
        unknown_ingredients: List[Dict[str, Any]],
        low_concern_ingredients: List[Dict[str, Any]],
        ingredient_summary: Dict[str, Any],
        product_category: str
    ) -> str:
        """
        Generate layman-friendly summary (1-3 sentences).
        
        Uses neutral, non-alarmist language understandable by non-experts.
        """
        sentences = []
        
        # First sentence: Overall assessment
        if verdict == "Generally Safe":
            sentences.append(
                f"This product appears generally safe for most users based on available ingredient information."
            )
        elif verdict == "Context Dependent":
            sentences.append(
                f"This product's safety depends on individual factors and usage context."
            )
        else:  # Use With Caution
            sentences.append(
                f"This product contains ingredients that may require careful consideration before use."
            )
        
        # Second sentence: Key concerns or positive aspects
        flagged_count = len(flagged_ingredients)
        unknown_count = len(unknown_ingredients)
        known_count = ingredient_summary.get("known_assessed", 0) + ingredient_summary.get("known_low_concern", 0)
        
        if flagged_count > 0:
            if flagged_count == 1:
                ing_name = flagged_ingredients[0].get("name", "an ingredient")
                risk_level = flagged_ingredients[0].get("risk_level", "moderate")
                if risk_level == "high":
                    sentences.append(
                        f"One ingredient ({ing_name}) has been identified with higher safety concerns."
                    )
                else:
                    sentences.append(
                        f"One ingredient ({ing_name}) has moderate safety considerations."
                    )
            else:
                sentences.append(
                    f"{flagged_count} ingredients have been identified with safety considerations."
                )
        elif known_count > 0:
            sentences.append(
                f"All identified ingredients have been assessed and show no significant safety concerns."
            )
        
        # Third sentence: Data completeness or recommendations
        if unknown_count > 0:
            if unknown_count == 1:
                sentences.append(
                    f"One ingredient could not be assessed due to insufficient safety data."
                )
            else:
                sentences.append(
                    f"{unknown_count} ingredients could not be fully assessed due to limited safety data."
                )
        elif flagged_count == 0 and known_count > 0:
            sentences.append(
                f"All ingredients in this product have been evaluated against current safety standards."
            )
        
        # Join sentences (limit to 3 sentences max)
        return " ".join(sentences[:3])
    
    def _identify_key_factors(
        self,
        flagged_ingredients: List[Dict[str, Any]],
        unknown_ingredients: List[Dict[str, Any]],
        ingredient_summary: Dict[str, Any],
        safety_score: int
    ) -> List[str]:
        """
        Identify up to 3 key contributing factors to the safety assessment.
        
        Prioritizes:
        1. High-risk flagged ingredients
        2. Dosage concerns
        3. Data completeness (unknown ingredients)
        4. Overall ingredient assessment status
        """
        factors = []
        
        # Factor 1: High-risk ingredients
        high_risk_ingredients = [
            ing for ing in flagged_ingredients 
            if ing.get("risk_level", "").lower() == "high"
        ]
        if high_risk_ingredients:
            if len(high_risk_ingredients) == 1:
                factors.append(
                    f"Contains {high_risk_ingredients[0].get('name', 'an ingredient')} with high safety concerns"
                )
            else:
                factors.append(
                    f"Contains {len(high_risk_ingredients)} ingredients with high safety concerns"
                )
        
        # Factor 2: Dosage concerns (check in all_ingredients for dosage_exceeded)
        # Note: dosage_exceeded might not be in flagged_ingredients format
        # Check if any flagged ingredients have safe_dosage set (indicates dosage awareness)
        dosage_aware_ingredients = [
            ing for ing in flagged_ingredients
            if ing.get("safe_dosage") is not None
        ]
        if dosage_aware_ingredients:
            factors.append(
                "Some ingredients may be present at concentrations requiring attention"
            )
        
        # Factor 3: Data completeness
        unknown_count = len(unknown_ingredients)
        total_ingredients = ingredient_summary.get("total", 0)
        if unknown_count > 0 and total_ingredients > 0:
            unknown_ratio = unknown_count / total_ingredients
            if unknown_ratio > 0.5:
                factors.append(
                    f"More than half of ingredients lack sufficient safety data for complete assessment"
                )
            elif unknown_ratio > 0.25:
                factors.append(
                    f"Some ingredients ({unknown_count}) lack sufficient safety data"
                )
            else:
                factors.append(
                    f"Limited safety data available for {unknown_count} ingredient(s)"
                )
        
        # Factor 4: Moderate risk ingredients (if no high risk)
        if not high_risk_ingredients and flagged_ingredients:
            moderate_count = len([
                ing for ing in flagged_ingredients
                if ing.get("risk_level", "").lower() == "moderate"
            ])
            if moderate_count > 0:
                factors.append(
                    f"{moderate_count} ingredient(s) with moderate safety considerations"
                )
        
        # Factor 5: Overall assessment quality
        if not factors and total_ingredients > 0:
            known_count = ingredient_summary.get("known_assessed", 0) + ingredient_summary.get("known_low_concern", 0)
            if known_count == total_ingredients:
                factors.append(
                    "All ingredients have been assessed with available safety data"
                )
        
        # Return up to 3 factors
        return factors[:3]
