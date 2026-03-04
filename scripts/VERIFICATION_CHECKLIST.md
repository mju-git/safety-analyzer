# Verification Checklist

## ✅ Completed Code Changes

1. **Unknown Ingredients Handling**
   - ✅ Changed `risk_level` from "low" to "unknown" for unknown ingredients
   - ✅ Added "unknown" to RISK_PENALTIES in safety engine
   - ✅ Updated frontend to display "unknown" (not "unknown risk")
   - ✅ Added CSS styling for unknown risk badge

2. **Required Fields in Output**
   - ✅ `risk_level` - included in flagged ingredients
   - ✅ `confidence` - included in flagged ingredients  
   - ✅ `notes` - included in flagged ingredients
   - ✅ `sources` - included in flagged ingredients (as `sources` array and `evidence_source`)

## 📋 Steps to Verify

### Step 1: Run Migration (if not done)
```bash
python scripts/migrate_ingredients_table.py
```

### Step 2: Run Seed Script
```bash
python scripts/seed_ingredient_knowledge_base.py
```

This populates the database with:
- Sodium Lauryl Sulfate (with aliases: SLS, SDS, etc.)
- Fragrance (with aliases: Parfum, Aroma, etc.)
- Parabens (with aliases: Methylparaben, Propylparaben, etc.)
- Caffeine (with aliases: Theine, Guaranine, etc.)
- Phosphoric Acid (with aliases: Orthophosphoric Acid, E338)

### Step 3: Verify Ingredient Lookup
```bash
python scripts/verify_ingredient_lookup.py
```

Expected output:
- ✅ Should find at least 5 ingredients (by name or alias)
- ✅ Should show confidence, sources, and notes for found ingredients
- ✅ Should correctly identify unknown ingredients

### Step 4: Test Product Analysis
```bash
python scripts/test_product_analysis.py
```

This will:
- Find a product with ingredients
- Run analysis
- Display the full JSON response
- Verify all required fields are present:
  - ✅ `risk_level` in flagged ingredients
  - ✅ `confidence` in flagged ingredients
  - ✅ `notes` in flagged ingredients
  - ✅ `sources` in flagged ingredients
- ✅ Verify unknown ingredients show `risk_level="unknown"` and `confidence="unknown"`

### Step 5: Test in Frontend

1. Start the backend:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Test with a product that has ingredients:
   - Search for a product (e.g., "cola", "toothpaste")
   - Click on the product
   - Verify the analysis shows:
     - ✅ Safety score
     - ✅ Flagged ingredients with:
       - Risk level badge (low/moderate/high/unknown)
       - Confidence badge (high/medium/low/unknown)
       - Notes section
       - Sources
     - ✅ Unknown ingredients show "unknown" (not "low risk" or "safe")

## 🔍 What to Check

### For Known Ingredients:
- `risk_level`: Should be "low", "moderate", or "high"
- `confidence`: Should be "high", "medium", or "low"
- `notes`: Should contain dosage, formulation, or population sensitivity info
- `sources`: Should be a list of authoritative sources (e.g., ["EFSA", "SCCS"])

### For Unknown Ingredients:
- `risk_level`: Should be **"unknown"** (not "low", "moderate", or "high")
- `confidence`: Should be **"unknown"**
- `notes`: Should mention "Ingredient not found in knowledge base"
- `sources`: Should be empty array `[]` or `null`

## 🐛 Troubleshooting

If verification fails:

1. **Ingredient lookup fails:**
   - Check if seed script ran successfully
   - Verify database has `ingredients` table with data
   - Check if migration added `aliases`, `confidence`, `sources` columns

2. **Analysis fails:**
   - Check backend logs for errors
   - Verify products have `ingredients_raw` field populated
   - Check browser console for frontend errors

3. **Unknown ingredients show wrong values:**
   - Verify code changes were applied
   - Check that `is_unknown=True` is being set correctly
   - Verify safety engine handles "unknown" risk_level
