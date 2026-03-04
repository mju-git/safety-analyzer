# Database Seeding Scripts

## seed_ingredients.py

Seeds the database with 10 example ingredients and their safety profiles for testing.

### Usage

```bash
# From the project root directory
python scripts/seed_ingredients.py
```

### What it does

- Creates 10 diverse ingredients covering different categories:
  - Water (solvent)
  - Sodium Chloride (preservative)
  - Citric Acid (preservative)
  - Sodium Hydroxide (pH adjuster)
  - Titanium Dioxide (colorant)
  - BHT (antioxidant)
  - Propylene Glycol (humectant)
  - Parabens (preservative)
  - Vitamin C (antioxidant)
  - Sodium Lauryl Sulfate (surfactant)

- Each ingredient includes:
  - Basic information (name, INCI name, CAS number, category)
  - Evidence strength
  - Notes
  - One or more safety profiles with:
    - Exposure route (skin, ingestion, inhalation)
    - Safe limits and units
    - Risk levels (low, moderate, high)
    - Population risk categories
    - Safety summaries
    - Evidence sources (EFSA, SCCS, CIR)

### Features

- **Idempotent**: Skips ingredients that already exist
- **Safe to run multiple times**: Won't create duplicates
- **Comprehensive**: Includes various risk levels and exposure routes
- **Realistic**: Based on real ingredient safety data

### Requirements

- Database must be set up and accessible
- `.env` file must contain `DATABASE_URL`
- Database tables must exist (run migrations or create tables first)
