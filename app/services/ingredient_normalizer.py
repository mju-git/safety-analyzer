"""Ingredient normalizer service for cleaning and matching ingredients with aliases."""
from typing import List, Dict, Optional, Tuple
import re
import json
import logging
from sqlalchemy.orm import Session

from app.models import Ingredient

# Set up logger
logger = logging.getLogger(__name__)


def normalize_string(text: str) -> str:
    """
    Normalize an ingredient string for matching.
    
    Steps:
    1. Lowercase
    2. Trim whitespace
    3. Remove punctuation (except alphanumeric and spaces)
    4. Normalize multiple spaces to single space
    
    Args:
        text: Raw ingredient string
        
    Returns:
        Normalized string for matching
        
    Example:
        >>> normalize_string("  Sodium Lauryl Sulfate,  ")
        'sodium lauryl sulfate'
        
        >>> normalize_string("SLS (Sodium Dodecyl Sulfate)")
        'sls sodium dodecyl sulfate'
    """
    if not text:
        return ""
    
    # Step 1: Lowercase
    normalized = text.lower()
    
    # Step 2: Trim whitespace
    normalized = normalized.strip()
    
    # Step 3: Remove punctuation (keep alphanumeric and spaces)
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    
    # Step 4: Normalize multiple spaces to single space
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized.strip()


def parse_ingredient_list(raw_text: str) -> List[str]:
    """
    Parse a raw ingredient string into a list of individual ingredient strings.
    
    Handles:
    - Multiple separators (commas, semicolons, newlines, slashes)
    - Parentheses (extracts content, handles both formats)
    - Percentages and regulatory phrases (strips them)
    - Preserves original text structure for traceability
    
    Args:
        raw_text: Raw ingredient string (e.g., "Water, Sodium Chloride (NaCl), Citric Acid <2%")
    
    Returns:
        List of normalized ingredient strings
        
    Example:
        >>> parse_ingredient_list("Water, Sodium Chloride (NaCl), Citric Acid <2%")
        ['water', 'sodium chloride', 'citric acid']
    """
    if not raw_text:
        return []
    
    # Step 1: Remove regulatory phrases and percentages
    # Common patterns: "may contain", "less than X%", "<X%", "contains X%", etc.
    regulatory_patterns = [
        r'\b(may contain|contains|less than|more than|up to|max|maximum|min|minimum)\s*\d*\.?\d*\s*%',
        r'<.*?>',  # Remove content in angle brackets like <2%
        r'\(.*?%.*?\)',  # Remove parentheses with percentages like "(<2%)"
        r'\b\d+\.?\d*\s*%',  # Standalone percentages
        r'\b(and|or)\s+their\s+salts',  # Common regulatory phrase
        r'\b(and|or)\s+derivatives',  # Common regulatory phrase
    ]
    
    cleaned_text = raw_text
    for pattern in regulatory_patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
    
    # Step 2: Handle parentheses - extract content but keep main ingredient
    # Pattern: "Ingredient (Alternative Name)" -> "Ingredient Alternative Name"
    # But also handle: "Ingredient (E123)" -> "Ingredient"
    cleaned_text = re.sub(r'\(([^)]+)\)', r' \1 ', cleaned_text)
    
    # Step 3: Split by multiple separators (commas, semicolons, newlines, slashes)
    # Handle both single and multiple separators
    separators = r'[,;\n\r/|]+'
    ingredients = re.split(separators, cleaned_text)
    
    # Step 4: Clean and normalize each ingredient
    normalized = []
    for ing in ingredients:
        # Remove leading/trailing whitespace
        ing = ing.strip()
        
        # Remove any remaining regulatory phrases
        ing = re.sub(r'\b(may contain|contains|less than|more than)\b', '', ing, flags=re.IGNORECASE)
        
        # Remove E-numbers in parentheses (e.g., "Citric Acid (E330)")
        ing = re.sub(r'\s*\(E\d+\)', '', ing, flags=re.IGNORECASE)
        
        # Remove CAS numbers (format: XXX-XX-X or XXX-XX-XX)
        ing = re.sub(r'\s*\d{2,7}-\d{2}-\d{1,2}', '', ing)
        
        # Normalize the string
        normalized_str = normalize_string(ing)
        
        # Filter out very short strings (likely artifacts) and common non-ingredients
        if normalized_str and len(normalized_str) > 2:
            # Skip common non-ingredient phrases
            skip_phrases = ['ingredients', 'contains', 'may contain', 'allergen', 'free from']
            if not any(phrase in normalized_str for phrase in skip_phrases):
                normalized.append(normalized_str)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_normalized = []
    for ing in normalized:
        if ing not in seen:
            seen.add(ing)
            unique_normalized.append(ing)
    
    return unique_normalized


def match_ingredient(
    db: Session,
    normalized_name: str
) -> Optional[Tuple[Ingredient, str, float]]:
    """
    Match a normalized ingredient name against the knowledge base.
    
    Searches in order:
    1. Exact name match (normalized) - confidence: 1.0
    2. INCI name match (normalized) - confidence: 0.95
    3. Alias match (normalized, checks JSON array) - confidence: 0.9
    4. Partial match for base ingredients - confidence: 0.7
    
    Args:
        db: Database session
        normalized_name: Normalized ingredient name to match
        
    Returns:
        Tuple of (Ingredient object, match_type, confidence) if found, None otherwise
        match_type: "name", "inci", "alias", or "partial"
        confidence: float between 0.0 and 1.0
    """
    if not normalized_name:
        logger.debug(f"match_ingredient: Empty normalized name provided")
        return None
    
    logger.debug(f"match_ingredient: Attempting to match '{normalized_name}'")
    
    # Get all ingredients and normalize their names for comparison
    all_ingredients = db.query(Ingredient).all()
    logger.debug(f"match_ingredient: Checking against {len(all_ingredients)} ingredients in knowledge base")
    
    # Step 1: Try exact name match (normalized) - Highest confidence
    for ingredient in all_ingredients:
        if ingredient.name:
            normalized_db_name = normalize_string(ingredient.name)
            if normalized_db_name == normalized_name:
                logger.info(f"match_ingredient: ✅ RESOLVED (name) '{normalized_name}' → '{ingredient.name}' (confidence: 1.0)")
                return (ingredient, "name", 1.0)
    
    # Step 2: Try INCI name match (normalized) - High confidence
    for ingredient in all_ingredients:
        if ingredient.inci_name:
            normalized_inci = normalize_string(ingredient.inci_name)
            if normalized_inci == normalized_name:
                logger.info(f"match_ingredient: ✅ RESOLVED (INCI) '{normalized_name}' → '{ingredient.name}' (confidence: 0.95)")
                return (ingredient, "inci", 0.95)
    
    # Step 3: Try alias match (normalized) - Good confidence
    for ingredient in all_ingredients:
        if ingredient.aliases:
            # Handle both list and JSON string formats
            aliases = ingredient.aliases
            if isinstance(aliases, str):
                try:
                    aliases = json.loads(aliases)
                except (json.JSONDecodeError, TypeError):
                    continue
            
            if isinstance(aliases, list):
                # Normalize each alias and check for match
                for alias in aliases:
                    if isinstance(alias, str):
                        normalized_alias = normalize_string(alias)
                        if normalized_alias == normalized_name:
                            logger.info(f"match_ingredient: ✅ RESOLVED (alias) '{normalized_name}' → '{ingredient.name}' via alias '{alias}' (confidence: 0.9)")
                            return (ingredient, "alias", 0.9)
    
    # Step 4: Try partial match for base ingredients - Lower confidence (inferred)
    # This handles cases like "Purified Water" matching "Water", "Water (Aqua)" matching "Water"
    # Only match if the normalized name contains the base ingredient name as a complete word
    for ingredient in all_ingredients:
        if ingredient.name:
            normalized_base = normalize_string(ingredient.name)
            # Check if normalized_name contains the base ingredient as a word
            # Use word boundaries to avoid partial matches (e.g., "water" in "watermelon")
            words_in_name = normalized_name.split()
            if normalized_base in words_in_name:
                # Additional check: ensure it's a base ingredient (low risk, high confidence)
                # This prevents false matches for complex ingredients
                if ingredient.confidence:
                    confidence_value = ingredient.confidence.value if hasattr(ingredient.confidence, 'value') else str(ingredient.confidence)
                    if confidence_value in ["high", "HIGH"]:
                        # Check if it's a low-risk base ingredient
                        safety_profiles = ingredient.ingredient_safety
                        if safety_profiles:
                            # Check if all safety profiles are low risk
                            all_low_risk = all(
                                profile.risk_level.value == "low" if hasattr(profile.risk_level, 'value') else str(profile.risk_level) == "low"
                                for profile in safety_profiles
                            )
                            if all_low_risk:
                                logger.info(f"match_ingredient: ⚠️ RESOLVED_INFERRED (partial) '{normalized_name}' → '{ingredient.name}' (confidence: 0.7)")
                                return (ingredient, "partial", 0.7)
                        else:
                            # If no safety profiles but high confidence, assume it's a base ingredient
                            logger.info(f"match_ingredient: ⚠️ RESOLVED_INFERRED (partial) '{normalized_name}' → '{ingredient.name}' (confidence: 0.7)")
                            return (ingredient, "partial", 0.7)
    
    logger.warning(f"match_ingredient: ❌ UNRESOLVED '{normalized_name}' - No match found in knowledge base")
    return None


def _generate_match_explanation(
    original_name: str,
    canonical_name: Optional[str],
    match_type: Optional[str],
    resolution_state: str,
    confidence: float
) -> str:
    """
    Generate a human-readable explanation of how an ingredient was matched.
    
    Args:
        original_name: The normalized name from the product
        canonical_name: The canonical name from knowledge base (if matched)
        match_type: How the match was made (name, inci, alias, partial, or None)
        resolution_state: resolved, resolved_inferred, or unresolved
        confidence: Confidence score (0.0-1.0)
        
    Returns:
        Human-readable explanation string
    """
    if resolution_state == "unresolved":
        return f"'{original_name}' was not found in the safety knowledge base. No safety assessment is available for this ingredient."
    
    if not canonical_name:
        return f"Match found for '{original_name}' but canonical name unavailable."
    
    confidence_pct = int(confidence * 100)
    
    if match_type == "name":
        return f"'{original_name}' matched exactly to canonical ingredient '{canonical_name}' (confidence: {confidence_pct}%)."
    elif match_type == "inci":
        return f"'{original_name}' matched via INCI name to '{canonical_name}' (confidence: {confidence_pct}%)."
    elif match_type == "alias":
        return f"'{original_name}' matched via alias to canonical ingredient '{canonical_name}' (confidence: {confidence_pct}%)."
    elif match_type == "partial":
        return f"'{original_name}' inferred to match '{canonical_name}' based on partial name match (confidence: {confidence_pct}%). This is a lower-confidence match."
    else:
        return f"'{original_name}' matched to '{canonical_name}' (confidence: {confidence_pct}%)."


def normalize_and_match_ingredients(
    db: Session,
    raw_text: str
) -> List[Dict[str, any]]:
    """
    Normalize ingredient strings and match them against the knowledge base.
    
    This is the main function that:
    1. Parses the raw ingredient string
    2. Normalizes each ingredient name
    3. Matches against knowledge base (name, INCI, aliases)
    4. Returns canonical ingredient IDs with resolution states and confidence
    
    Args:
        db: Database session
        raw_text: Raw ingredient string from product
        
    Returns:
        List of dicts with keys:
            - ingredient_id: Canonical ingredient ID (None if unresolved)
            - canonical_name: Canonical ingredient name (None if unresolved)
            - original_name: Original normalized name from product
            - match_type: "name", "inci", "alias", "partial", or None
            - resolution_state: "resolved", "resolved_inferred", or "unresolved"
            - confidence: float between 0.0 and 1.0
            - match_explanation: Human-readable explanation of how match was made
            - is_unknown: True if unresolved (for backward compatibility)
    """
    logger.info(f"normalize_and_match_ingredients: Starting normalization for raw text: '{raw_text[:100]}...'")
    
    # Parse and normalize ingredient strings
    normalized_names = parse_ingredient_list(raw_text)
    logger.info(f"normalize_and_match_ingredients: Parsed {len(normalized_names)} ingredients: {normalized_names}")
    
    results = []
    for normalized_name in normalized_names:
        logger.debug(f"normalize_and_match_ingredients: Processing ingredient '{normalized_name}'")
        
        # Try to match against knowledge base
        match_result = match_ingredient(db, normalized_name)
        
        if match_result:
            ingredient, match_type, confidence = match_result
            
            # Determine resolution state based on match type and confidence
            if match_type == "partial":
                resolution_state = "resolved_inferred"
            else:
                resolution_state = "resolved"
            
            # Generate match explanation
            match_explanation = _generate_match_explanation(
                normalized_name,
                ingredient.name,
                match_type,
                resolution_state,
                confidence
            )
            
            result = {
                "ingredient_id": ingredient.id,
                "canonical_name": ingredient.name,
                "original_name": normalized_name,
                "match_type": match_type,
                "resolution_state": resolution_state,
                "confidence": confidence,
                "match_explanation": match_explanation,
                "is_unknown": False  # Backward compatibility
            }
            
            logger.debug(f"normalize_and_match_ingredients: {resolution_state.upper()} '{normalized_name}' → '{ingredient.name}' (confidence: {confidence:.2f}, match: {match_type})")
            results.append(result)
        else:
            # Not found - explicitly mark as unresolved
            match_explanation = _generate_match_explanation(
                normalized_name,
                None,
                None,
                "unresolved",
                0.0
            )
            
            result = {
                "ingredient_id": None,
                "canonical_name": None,
                "original_name": normalized_name,
                "match_type": None,
                "resolution_state": "unresolved",
                "confidence": 0.0,
                "match_explanation": match_explanation,
                "is_unknown": True  # Backward compatibility
            }
            
            logger.warning(f"normalize_and_match_ingredients: UNRESOLVED '{normalized_name}' - No match found")
            results.append(result)
    
    # Log summary
    resolved_count = sum(1 for r in results if r["resolution_state"] == "resolved")
    inferred_count = sum(1 for r in results if r["resolution_state"] == "resolved_inferred")
    unresolved_count = sum(1 for r in results if r["resolution_state"] == "unresolved")
    
    logger.info(f"normalize_and_match_ingredients: Summary - Resolved: {resolved_count}, Inferred: {inferred_count}, Unresolved: {unresolved_count}")
    
    return results


# Backward compatibility function
def normalize_ingredients(raw_text: str) -> List[str]:
    """
    Legacy function for backward compatibility.
    
    Returns list of normalized ingredient names (not IDs).
    Use normalize_and_match_ingredients() for new code.
    """
    return parse_ingredient_list(raw_text)
