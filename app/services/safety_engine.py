from typing import List, Dict, Any, Optional


class SafetyEngine:
    """
    Explainable safety scoring engine.
    Produces a score (0–100) and human-readable explanations.
    """

    BASE_SCORE = 100

    RISK_PENALTIES = {
        "low": 0,
        "moderate": 10,
        "high": 20,
        "unknown": 0  # Unknown ingredients do NOT affect score, only confidence
    }

    USER_PROFILE_PENALTIES = {
        "sensitive_skin": 10,
        "pregnant": 15,
        "child": 15
    }

    def _calculate_confidence(
        self,
        has_safety_data: bool,
        has_source: bool,
        has_safe_limit: bool,
        has_summary: bool,
        is_unknown: bool
    ) -> str:
        """
        Calculate confidence level for ingredient assessment.
        
        Returns: "high", "medium", "low", or "unknown"
        """
        if is_unknown:
            return "unknown"
        
        if not has_safety_data:
            return "low"
        
        # High confidence: has source, safe limit, and summary
        if has_source and has_safe_limit and has_summary:
            return "high"
        
        # Medium confidence: has source and either safe limit or summary
        if has_source and (has_safe_limit or has_summary):
            return "medium"
        
        # Low confidence: has safety data but limited information
        if has_safety_data:
            return "low"
        
        return "unknown"

    def _generate_evidence_explanation(
        self,
        ingredient: Dict[str, Any]
    ) -> str:
        """
        Generate explanation of evidence backing the risk assessment.
        
        Returns a string explaining:
        - Why the claim is made (source)
        - How strong the evidence is (evidence strength)
        - Reference information if available
        """
        evidence_parts = []
        
        evidence_source = ingredient.get("evidence_source")
        evidence_strength = ingredient.get("evidence_strength")
        evidence_reference_id = ingredient.get("evidence_reference_id")
        evidence_document_name = ingredient.get("evidence_document_name")
        
        if evidence_source:
            evidence_parts.append(f"Evidence source: {evidence_source}")
        
        if evidence_strength:
            strength_desc = {
                "high": "strong",
                "medium": "moderate",
                "low": "limited"
            }.get(evidence_strength.lower(), evidence_strength)
            evidence_parts.append(f"Evidence strength: {strength_desc}")
        
        if evidence_reference_id:
            evidence_parts.append(f"Reference: {evidence_reference_id}")
        
        if evidence_document_name:
            evidence_parts.append(f"Document: {evidence_document_name}")
        
        if evidence_parts:
            return " | ".join(evidence_parts)
        
        return ""

    def _generate_notes(
        self,
        ingredient: Dict[str, Any],
        dosage_issue: bool,
        user_profile: Dict[str, bool],
        is_unknown: bool
    ) -> str:
        """
        Generate notes explaining dosage, formulation, or population sensitivity.
        """
        notes = []
        
        if is_unknown:
            notes.append("⚠️ UNCERTAINTY: Ingredient not found in safety database. Assessment based on limited information and should be interpreted with caution. Safety data may be incomplete.")
            return " ".join(notes)
        
        # Dosage notes
        safe_limit = ingredient.get("safe_limit")
        est_conc = ingredient.get("estimated_concentration")
        
        if safe_limit is not None:
            if est_conc is not None:
                if dosage_issue:
                    notes.append(
                        f"Concentration ({est_conc} {ingredient.get('unit', '')}) exceeds safe limit "
                        f"({safe_limit} {ingredient.get('unit', '')})."
                    )
                else:
                    notes.append(
                        f"Concentration ({est_conc} {ingredient.get('unit', '')}) is within safe limits "
                        f"({safe_limit} {ingredient.get('unit', '')})."
                    )
            else:
                notes.append(
                    f"Safe limit established at {safe_limit} {ingredient.get('unit', '')}, "
                    "but product concentration is unknown."
                )
        elif est_conc is not None:
            notes.append(
                f"Product contains {est_conc} {ingredient.get('unit', '')}, "
                "but no safe limit data available for comparison."
            )
        else:
            notes.append("Dosage information not available. Assessment based on general safety profile.")
        
        # Population sensitivity notes
        population_risk = ingredient.get("population_risk", "general")
        if user_profile:
            if user_profile.get("sensitive_skin") and population_risk == "sensitive_skin":
                notes.append("May cause irritation in individuals with sensitive skin.")
            if user_profile.get("pregnant") and population_risk == "pregnancy":
                notes.append("Special considerations apply during pregnancy. Consult healthcare provider.")
            if user_profile.get("child") and population_risk == "children":
                notes.append("Use age-appropriate formulations for children.")
        
        # Formulation notes
        exposure_route = ingredient.get("exposure_route", "skin")
        if exposure_route:
            notes.append(f"Assessment based on {exposure_route} exposure route.")
        
        return " ".join(notes) if notes else "No additional notes available."

    def analyze(
        self,
        ingredients: List[Dict[str, Any]],
        user_profile: Dict[str, bool] | None = None
    ) -> Dict[str, Any]:
        """
        Analyze ingredients and produce safety score with detailed assessments.
        
        ingredients: list of dicts with keys:
            - name
            - risk_level (low/moderate/high)
            - exposure_route
            - safe_limit
            - estimated_concentration
            - population_risk
            - summary
            - source
            - is_unknown (optional, indicates ingredient not in database)
        """

        score = self.BASE_SCORE
        explanations = []
        flagged_ingredients = []  # Class 1: Known & assessed (moderate/high risk)
        low_concern_ingredients = []  # Class 2: Known but low concern
        positive_ingredients = []  # Backward compatibility
        unknown_ingredients = []  # Class 3: Unknown/insufficient data
        all_ingredients = []  # Track ALL ingredients for complete output

        user_profile = user_profile or {}

        for ing in ingredients:
            name = ing.get("name", "Unknown")
            risk = ing.get("risk_level", "unknown")  # Default to unknown if not specified
            safe_limit = ing.get("safe_limit")
            est_conc = ing.get("estimated_concentration")
            population_risk = ing.get("population_risk", "general")
            is_unknown = ing.get("is_unknown", False)
            resolution_state = ing.get("resolution_state", "unresolved" if is_unknown else "resolved")
            has_source = ing.get("source") is not None
            has_summary = ing.get("summary") is not None
            has_safe_limit = safe_limit is not None

            # Use stored confidence from knowledge base if available, otherwise calculate
            stored_confidence = ing.get("confidence")
            if stored_confidence:
                confidence = stored_confidence
            else:
                # Calculate confidence level if not provided
                confidence = self._calculate_confidence(
                    has_safety_data=not is_unknown and (has_source or has_summary),
                    has_source=has_source,
                    has_safe_limit=has_safe_limit,
                    has_summary=has_summary,
                    is_unknown=is_unknown
                )

            # IMPORTANT: Unresolved ingredients do NOT affect score, only confidence
            # Also, resolved_inferred ingredients should have reduced impact on scoring
            if resolution_state == "unresolved" or is_unknown or risk == "unknown":
                ingredient_penalty = 0  # No penalty for unresolved ingredients
            elif resolution_state == "resolved_inferred":
                # Reduced penalty for inferred matches (multiply by confidence)
                base_penalty = self.RISK_PENALTIES.get(risk, 0)
                resolution_confidence = ing.get("resolution_confidence", 0.7)
                ingredient_penalty = int(base_penalty * resolution_confidence)
            else:
                # Full penalty for fully resolved ingredients
                ingredient_penalty = self.RISK_PENALTIES.get(risk, 0)

            # Dosage awareness
            dosage_issue = False
            if safe_limit is not None and est_conc is not None:
                if est_conc > safe_limit:
                    ingredient_penalty += 30
                    dosage_issue = True

            # User profile adjustment
            profile_penalty = 0
            profile_notes = []
            for profile, active in user_profile.items():
                if active and profile in population_risk:
                    profile_penalty += self.USER_PROFILE_PENALTIES.get(profile, 0)

            total_penalty = ingredient_penalty + profile_penalty
            # Only subtract penalty if ingredient is resolved (unresolved don't affect score)
            if resolution_state != "unresolved" and not is_unknown and risk != "unknown":
                score -= total_penalty

            # Use stored notes from knowledge base if available, otherwise generate
            stored_notes = ing.get("notes")
            if resolution_state == "unresolved" or is_unknown:
                # For unresolved ingredients, ensure clear uncertainty notes
                uncertainty_note = "⚠️ UNCERTAINTY: This ingredient was not found in the safety knowledge base. Assessment is based on limited information and should be interpreted with caution. Safety data may be incomplete."
                if stored_notes:
                    notes = f"{uncertainty_note} {stored_notes}"
                else:
                    notes = uncertainty_note
            elif stored_notes:
                # Use stored notes as base, append generated notes if needed
                generated_notes = self._generate_notes(ing, dosage_issue, user_profile, is_unknown)
                # Combine if generated notes add new information
                if generated_notes and generated_notes not in stored_notes:
                    # Only append if generated notes provide additional context
                    if "Dosage information" in generated_notes or "Population sensitivity" in generated_notes:
                        notes = f"{stored_notes} {generated_notes}"
                    else:
                        notes = stored_notes
                else:
                    notes = stored_notes
            else:
                # Generate notes if not available from knowledge base
                notes = self._generate_notes(ing, dosage_issue, user_profile, is_unknown)

            # Get sources - prefer list from knowledge base, fallback to single source
            sources = ing.get("sources", [])
            if not sources:
                single_source = ing.get("source")
                if single_source:
                    sources = [single_source]
            
            # Generate evidence explanation
            evidence_explanation = self._generate_evidence_explanation(ing)
            
            # Build ingredient assessment
            assessment = {
                "name": name,
                "risk_level": risk,
                "confidence": confidence,
                "safe_limit": safe_limit,
                "unit": ing.get("unit"),  # Preserve unit for response
                "estimated_concentration": est_conc,
                "population_risk": population_risk,
                "dosage_exceeded": dosage_issue,
                "explanation": ing.get("summary"),
                "source": ing.get("source"),  # Primary source for backward compatibility
                "sources": sources,  # List of all authoritative sources
                "notes": notes,  # Notes from knowledge base or generated
                "is_unknown": is_unknown,  # Backward compatibility
                "resolution_state": resolution_state,  # resolved, resolved_inferred, or unresolved
                "resolution_confidence": ing.get("resolution_confidence", 1.0 if resolution_state == "resolved" else (0.7 if resolution_state == "resolved_inferred" else 0.0)),
                "match_explanation": ing.get("match_explanation", ""),  # Explanation of how match was made
                # Evidence-backed risk attribution
                "evidence_source": ing.get("evidence_source"),
                "evidence_reference_id": ing.get("evidence_reference_id"),
                "evidence_document_name": ing.get("evidence_document_name"),
                "evidence_strength": ing.get("evidence_strength"),
                "evidence_explanation": evidence_explanation  # Human-readable evidence explanation
            }

            # Add to all_ingredients list - ensures every ingredient is included
            all_ingredients.append(assessment)
            
            # Three-class system:
            # 1. Known & assessed (moderate/high risk) -> flagged_ingredients
            # 2. Known but low concern (low risk, no penalty) -> low_concern_ingredients
            # 3. Unknown/insufficient data -> unknown_ingredients
            
            if is_unknown or risk == "unknown":
                # Class 3: Unknown/insufficient data
                unknown_ingredients.append(assessment)
                explanations.append(f"{name}: Insufficient data (not in knowledge base)")
            elif total_penalty > 0:
                # Class 1: Known & assessed (moderate/high risk)
                flagged_ingredients.append(assessment)
                explanations.append(
                    f"{name}: {risk} risk"
                    + (" (above safe limit)" if dosage_issue else "")
                )
            else:
                # Class 2: Known but low concern (low risk, no penalty)
                low_concern_ingredients.append(assessment)
                positive_ingredients.append(assessment)  # Keep for backward compatibility

        score = max(0, min(score, 100))
        
        # Calculate overall confidence based on unknowns
        total_ingredients = len(ingredients)
        unknown_count = len(unknown_ingredients)
        
        # Lower confidence if many unknowns
        overall_confidence = "high"
        if unknown_count > 0:
            unknown_ratio = unknown_count / total_ingredients if total_ingredients > 0 else 0
            if unknown_ratio > 0.5:
                overall_confidence = "low"
            elif unknown_ratio > 0.25:
                overall_confidence = "medium"
            else:
                overall_confidence = "medium"  # Some unknowns but mostly known

        recommendation = self._final_recommendation(score, unknown_ingredients, overall_confidence)

        return {
            "safety_score": score,
            "overall_confidence": overall_confidence,  # Confidence affected by unknowns
            "flagged_ingredients": flagged_ingredients,  # Class 1: Known & assessed
            "low_concern_ingredients": low_concern_ingredients,  # Class 2: Known but low concern
            "positive_ingredients": positive_ingredients,  # Backward compatibility
            "unknown_ingredients": unknown_ingredients,  # Class 3: Unknown/insufficient data
            "all_ingredients": all_ingredients,  # Complete list of all ingredients
            "explanations": explanations,
            "recommendation": recommendation,
            "ingredient_summary": {
                "total": total_ingredients,
                "known_assessed": len(flagged_ingredients),
                "known_low_concern": len(low_concern_ingredients),
                "unknown": unknown_count
            }
        }

    @staticmethod
    def _final_recommendation(score: int, unknown_ingredients: List[Dict[str, Any]], overall_confidence: str = "high") -> str:
        base_recommendation = ""
        if score >= 85:
            base_recommendation = "Low risk. Suitable for most users."
        elif score >= 65:
            base_recommendation = "Generally safe, with minor concerns depending on sensitivity."
        elif score >= 40:
            base_recommendation = "Moderate risk. Caution advised for sensitive users."
        else:
            base_recommendation = "High risk. Not recommended without professional advice."
        
        # Add confidence note based on unknowns
        if unknown_ingredients:
            unknown_count = len(unknown_ingredients)
            confidence_note = ""
            if overall_confidence == "low":
                confidence_note = f" Confidence: Low. {unknown_count} ingredient(s) have insufficient safety data. Assessment may be incomplete."
            elif overall_confidence == "medium":
                confidence_note = f" Confidence: Medium. {unknown_count} ingredient(s) have insufficient safety data."
            else:
                confidence_note = f" Note: {unknown_count} ingredient(s) have insufficient safety data."
            
            base_recommendation += confidence_note
        
        return base_recommendation
