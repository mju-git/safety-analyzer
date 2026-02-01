# Product Safety Analyzer – Web + App MVP

## Overview
This project is a product safety analysis system that evaluates items that are consumed or come into contact with the human body.
It supports food, cosmetics, household products, and supplements.

The system is accessible via:
- A web app (product search)
- A mobile app (product search + barcode scanning)

Both clients use the same backend and safety engine.

---

## Supported Input Methods

### MVP
- Product name search (web + app)
- Brand + product search (web + app)
- Barcode scan (app only)

### Future
- Ingredient list paste
- OCR camera scanning

---

## Core Principles
- Evidence-based and explainable
- Dosage- and exposure-aware
- No fear-based labeling
- Transparent uncertainty
- Ingredient safety database is core intellectual property
- Cache external data locally

---

## Architecture

Client (Web / Mobile)
  → FastAPI Backend
    → Product Resolver
    → Ingredient Normalizer
    → Safety Engine
    → PostgreSQL

---

## Tech Stack

### Backend
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- RapidFuzz (fuzzy matching)

### Frontend (Web MVP)
- Simple React or Next.js
- Search input
- Results page

(No frontend code generated in MVP backend phase.)

---

## Database Schema

### products
- id (PK)
- barcode (nullable, unique)
- name
- brand
- category (food, cosmetic, household, supplement)
- ingredients_raw
- source
- last_fetched
- created_at

### ingredients
- id (PK)
- name (unique)
- inci_name
- cas_number
- category
- evidence_strength (high, medium, low)
- notes

### ingredient_safety
- id (PK)
- ingredient_id (FK)
- exposure_route (skin, ingestion, inhalation)
- safe_limit
- unit
- risk_level (low, moderate, high)
- population_risk (general, sensitive_skin, pregnancy, children)
- summary
- source (EFSA, SCCS, CIR)

### product_ingredients
- product_id (FK)
- ingredient_id (FK)
- estimated_concentration (nullable)

### product_scores
- product_id (FK)
- safety_score (0–100)
- explanation (JSON)
- computed_at

---

## API Endpoints

### POST /scan/barcode
Used by mobile app only.

Input:
{
  "barcode": "string"
}

---

### GET /search/products
Used by web and app.

Query:
?q=string

Returns a list of matching products.

---

### POST /analyze/product
Used by web and app.

Input:
{
  "product_id": int,
  "user_profile": {
    "sensitive_skin": bool,
    "pregnant": bool,
    "child": bool
  }
}

---

### POST /analyze/by-name
Used by web and app.

Input:
{
  "name": "string",
  "brand": "optional string",
  "category": "optional string"
}

If product is not found locally:
- fetch from external sources
- store locally
- analyze

---

### GET /ingredient/{name}
Returns ingredient safety profile.

---

## Search Logic

1. Search local database using:
   - full-text search
   - fuzzy matching (RapidFuzz)
2. If confidence is high:
   - return product
3. If not found:
   - fetch from external APIs
   - store locally
   - return result

---

## Safety Scoring Logic

- Base score: 100
- Deduct points per ingredient based on:
  - risk level
  - exposure route
  - safe dosage limits
- Adjust score based on user profile
- Clamp final score between 0 and 100

---

## Expected Output

- Overall safety score
- Flagged ingredients with:
  - reason
  - safe dosage
  - exposure context
  - evidence source
- Beneficial ingredients
- Clear recommendation text

---

## Non-Goals (MVP)

- User accounts
- OCR camera scanning
- ML-based predictions
- Real-time study scraping
