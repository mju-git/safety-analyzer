# Product Safety Analyzer - FastAPI Backend

FastAPI backend scaffold for the Product Safety Analyzer system.

## Features

- **Product Search**: Web-based product search by name or brand
- **Barcode Scanning**: Optional barcode scanning (barcode nullable)
- **Shared Analysis Pipeline**: Unified analysis endpoints for web and mobile

## Project Structure

```
app/
├── __init__.py
├── main.py              # FastAPI application entry point
├── database.py          # Database connection and session management
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic request/response schemas
└── routers/
    ├── __init__.py
    ├── search.py        # Product search endpoints
    ├── barcode.py       # Barcode scanning endpoints
    └── analysis.py      # Product analysis endpoints
```

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure database**:
   - Copy `.env.example` to `.env`
   - Update `DATABASE_URL` with your PostgreSQL connection string

3. **Create database**:
   ```bash
   # Create PostgreSQL database
   createdb safety_scan
   ```

4. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`
   API documentation at `http://localhost:8000/docs`

## API Endpoints

### Search
- `GET /search/products?q={query}` - Search products by name or brand

### Barcode
- `POST /scan/barcode` - Search product by barcode

### Analysis
- `POST /analyze/product` - Analyze product by ID
- `POST /analyze/by-name` - Analyze product by name
- `GET /analyze/ingredient/{name}` - Get ingredient safety profile

## Database Models

- **products**: Product information with optional barcode
- **ingredients**: Ingredient master data
- **ingredient_safety**: Safety profiles for ingredients
- **product_ingredients**: Junction table linking products and ingredients
- **product_scores**: Computed safety scores for products

## Next Steps

- [ ] Implement external API fetching (OpenFoodFacts, etc.)
- [ ] Add fuzzy matching with RapidFuzz for search
- [ ] Implement safety scoring algorithm
- [ ] Add database migrations with Alembic
- [ ] Add input validation and error handling
- [ ] Add logging and monitoring

## Notes

- External API fetching is not yet implemented
- Safety scoring logic is placeholder
- Database tables are created automatically on startup (use Alembic for production)
