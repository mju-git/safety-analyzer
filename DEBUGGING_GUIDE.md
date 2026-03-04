# Debugging Guide: Product Analysis Not Showing

## Step-by-Step Debugging Process

### Step 1: Check Backend Logs

When you click on Colgate or Coca Cola, **immediately check the terminal where your FastAPI server is running**. Look for:

1. **Python traceback errors** (red text)
2. **Error messages** starting with "Error analyzing product"
3. **Any exception details**

**What to look for:**
- `AttributeError` - usually means a field doesn't exist
- `TypeError` - usually means wrong data type
- `KeyError` - usually means missing dictionary key
- `ProgrammingError` - usually means database column issue

### Step 2: Check Browser Console

1. Open your browser
2. Press **F12** to open DevTools
3. Go to the **Console** tab
4. Click on Colgate or Coca Cola
5. Look for:
   - Red error messages
   - "Analysis response:" logs (if they appear)
   - Network errors

### Step 3: Check Network Tab

1. In DevTools, go to the **Network** tab
2. Click on Colgate or Coca Cola
3. Find the request to `/analyze/product`
4. Click on it
5. Check:
   - **Status Code**: Should be 200 (green) or 500 (red)
   - **Response** tab: See what the server actually returned
   - **Headers** tab: Check if request was sent correctly

### Step 4: Run Debug Scripts

Run these scripts in your **conda environment**:

#### A. Check Products in Database
```bash
python scripts/check_products_in_db.py
```

This shows:
- All products in your database
- Which ones have `ingredients_raw` filled
- Preview of ingredients

#### B. Debug Specific Product
```bash
python scripts/debug_product_analysis.py cola
```
or
```bash
python scripts/debug_product_analysis.py colgate
```

This will:
- Find the product
- Show its details
- Attempt analysis
- Show any errors with full traceback
- Display the analysis result if successful

### Step 5: Test API Directly

#### Option A: Using Swagger UI
1. Go to `http://localhost:8000/docs`
2. Find `/analyze/product` endpoint
3. Click "Try it out"
4. Enter the product ID (e.g., Cola's ID)
5. Click "Execute"
6. See the response

#### Option B: Using curl (Command Prompt)
```bash
curl -X POST "http://localhost:8000/analyze/product" -H "Content-Type: application/json" -d "{\"product_id\": 1, \"user_profile\": {}}"
```

Replace `1` with the actual product ID.

### Step 6: Check Database Structure

Run this SQL query in pgAdmin or psql:

```sql
-- Check if products exist and have ingredients
SELECT 
    id, 
    name, 
    brand,
    CASE 
        WHEN ingredients_raw IS NULL OR ingredients_raw = '' 
        THEN 'NO INGREDIENTS' 
        ELSE 'HAS INGREDIENTS' 
    END as status,
    LENGTH(ingredients_raw) as ingredients_length
FROM products 
WHERE name ILIKE '%cola%' OR name ILIKE '%colgate%'
ORDER BY name;
```

### Step 7: Check Ingredient Knowledge Base

```sql
-- Check if ingredients table has data
SELECT COUNT(*) as total_ingredients FROM ingredients;

-- Check if confidence column exists
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'ingredients' AND column_name = 'confidence';
```

## Common Issues and Solutions

### Issue 1: "column ingredients.confidence does not exist"
**Solution:** Run migration script:
```bash
python scripts/migrate_ingredients_table.py
```

### Issue 2: "AttributeError: 'NoneType' object has no attribute 'value'"
**Solution:** Already fixed in code - confidence field now handles None properly.

### Issue 3: Products have ingredients but analysis fails
**Possible causes:**
- Ingredient names don't match knowledge base
- JSON parsing error in aliases/sources
- Missing safety profiles

**Check:**
```bash
python scripts/verify_ingredient_lookup.py
```

### Issue 4: Frontend shows blank page
**Possible causes:**
- API returns error (check Network tab)
- Frontend JavaScript error (check Console tab)
- Response structure doesn't match frontend expectations

**Check:**
- Browser Console for JavaScript errors
- Network tab for API response
- Backend logs for server errors

## Quick Diagnostic Commands

Run these in sequence:

```bash
# 1. Check products
python scripts/check_products_in_db.py

# 2. Debug specific product
python scripts/debug_product_analysis.py cola

# 3. Verify ingredient lookup
python scripts/verify_ingredient_lookup.py

# 4. Test full analysis
python scripts/test_product_analysis.py
```

## What to Report

If you still have issues, provide:

1. **Backend terminal output** - Copy the full error traceback
2. **Browser Console errors** - Screenshot or copy text
3. **Network tab response** - What status code and response body
4. **Product details** - Output from `check_products_in_db.py`
5. **Debug script output** - Output from `debug_product_analysis.py`

## Expected Behavior

When clicking on a product with ingredients:
1. Frontend sends POST to `/analyze/product` with product_id
2. Backend processes ingredients and looks them up
3. Backend returns JSON with:
   - `product_id`
   - `safety_score` (0-100)
   - `explanation` object with:
     - `flagged_ingredients` (array)
     - `beneficial_ingredients` (array)
     - `recommendation` (string)
   - `computed_at` (timestamp)
4. Frontend displays the analysis

If any step fails, the error should appear in backend logs or browser console.
