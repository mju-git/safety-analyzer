# Evidence-Backed Risk Attribution Implementation

## Overview
This milestone adds evidence-backed risk attribution to ingredient safety assessments, increasing trust and explainability by showing:
- **Why** a claim is made (evidence source)
- **How strong** the evidence is (evidence strength)
- **Where** the evidence comes from (reference ID and document name)

## Changes Made

### 1. Database Schema Extensions

**IngredientSafety Model** (`app/models.py`):
- Added `reference_id`: Reference ID or document identifier (e.g., "SCCS/1234/12", "EFSA-Q-2020-00123")
- Added `document_name`: Document name or title (e.g., "Opinion on Sodium Lauryl Sulfate")
- Added `evidence_strength`: Evidence strength for this specific safety profile (high/medium/low)

### 2. Migration Script

**`scripts/migrate_ingredient_safety_table.py`**:
- Adds the three new columns to the `ingredient_safety` table
- Handles existing databases gracefully (checks if columns exist before adding)
- Run with: `python scripts/migrate_ingredient_safety_table.py`

### 3. Seed Script Updates

**`scripts/seed_ingredient_knowledge_base.py`**:
- All safety profiles now include:
  - `reference_id`: Placeholder reference IDs (e.g., "SCCS/1234/12")
  - `document_name`: Placeholder document names
  - `evidence_strength`: Evidence strength enum (HIGH/MEDIUM/LOW)
- **Note**: Current references are placeholders. Replace with actual regulatory document references when available.

### 4. Safety Engine Enhancements

**`app/services/safety_engine.py`**:
- Added `_generate_evidence_explanation()` method:
  - Creates human-readable evidence explanations
  - Formats: "Evidence source: EFSA | Evidence strength: strong | Reference: EFSA-Q-2020-00123 | Document: Scientific Opinion on..."
- Evidence explanations are automatically appended to ingredient notes
- All ingredient assessments now include:
  - `evidence_source`: Primary evidence source
  - `evidence_reference_id`: Reference ID
  - `evidence_document_name`: Document name
  - `evidence_strength`: Evidence strength (high/medium/low)
  - `evidence_explanation`: Human-readable explanation

### 5. Analysis Router Updates

**`app/routers/analysis.py`**:
- Extracts evidence information from safety profiles
- Passes evidence data to safety engine
- Includes evidence fields in all ingredient responses:
  - `flagged_ingredients`
  - `all_ingredients`
  - `unknown_ingredients` (set to None for unknowns)

## Evidence Explanation Format

Evidence explanations are automatically generated and included in ingredient notes:

**Example for high-strength evidence:**
```
[Evidence: Evidence source: EFSA | Evidence strength: strong | Reference: EFSA-Q-2020-00123 | Document: Scientific Opinion on Sodium Lauryl Sulfate]
```

**Example for medium-strength evidence:**
```
[Evidence: Evidence source: SCCS | Evidence strength: moderate | Reference: SCCS/1234/12 | Document: Opinion on Fragrance Allergens]
```

**Example for unknown ingredients:**
```
(No evidence explanation - ingredient not found in knowledge base)
```

## Response Structure

Each ingredient in the analysis response now includes:

```json
{
    "name": "Sodium Lauryl Sulfate",
    "risk_level": "moderate",
    "confidence": "high",
    "evidence_source": "SCCS",
    "evidence_reference_id": "SCCS/1234/12",
    "evidence_document_name": "Opinion on Sodium Lauryl Sulfate",
    "evidence_strength": "high",
    "evidence_explanation": "Evidence source: SCCS | Evidence strength: strong | Reference: SCCS/1234/12 | Document: Opinion on Sodium Lauryl Sulfate",
    "notes": "... [Evidence: Evidence source: SCCS | Evidence strength: strong | Reference: SCCS/1234/12 | Document: Opinion on Sodium Lauryl Sulfate]"
}
```

## Usage Instructions

### 1. Run Migration
```bash
python scripts/migrate_ingredient_safety_table.py
```

### 2. Update Seed Data (Optional)
The seed script already includes placeholder references. To add real references:
- Edit `scripts/seed_ingredient_knowledge_base.py`
- Replace placeholder `reference_id` values with actual regulatory document IDs
- Replace placeholder `document_name` values with actual document titles
- Set appropriate `evidence_strength` values based on evidence quality

### 3. Re-seed Database (if needed)
```bash
python scripts/seed_ingredient_knowledge_base.py
```

## Design Principles

1. **No Invented Data**: All current references are clearly marked as placeholders
2. **Structured for Real Data**: System is ready to accept real regulatory references
3. **Transparent**: Evidence strength is clearly communicated (strong/moderate/limited)
4. **Explainable**: Users can see why claims are made and how strong the evidence is
5. **Backward Compatible**: Existing endpoints continue to work; new fields are optional

## Next Steps

1. **Replace Placeholders**: When real regulatory data is available, update seed script with actual references
2. **Enhance Explanations**: Consider adding links to source documents if available
3. **Evidence Quality**: Review and refine evidence strength assignments based on actual data quality
4. **Frontend Integration**: Update frontend to display evidence information prominently

## Testing

To verify the implementation:

1. Run migration script
2. Re-seed database (or update existing ingredients)
3. Analyze a product with known ingredients
4. Check response for:
   - `evidence_source` fields
   - `evidence_reference_id` fields
   - `evidence_document_name` fields
   - `evidence_strength` fields
   - `evidence_explanation` in notes

Example API call:
```bash
curl -X POST "http://localhost:8000/analyze/product" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1}'
```

Check the response for evidence fields in `explanation.flagged_ingredients` and `explanation.all_ingredients`.
