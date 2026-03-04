"""Main FastAPI application."""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import search, barcode, analysis
from app.database import engine, Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create database tables
# In production, use Alembic for migrations instead
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Product Safety Analyzer API",
    description="Backend API for product safety analysis system",
    version="0.1.0"
)

# Configure CORS
# In production, restrict origins to your frontend domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search.router)
app.include_router(barcode.router)
app.include_router(analysis.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Product Safety Analyzer API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
