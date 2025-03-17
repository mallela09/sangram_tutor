# sangram_tutor/main.py
import logging
import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Import API routers
from sangram_tutor.api.auth import router as auth_router
from sangram_tutor.api.users import router as users_router
from sangram_tutor.api.learning import router as learning_router
from sangram_tutor.api.analytics import router as analytics_router

# Import database components
from sangram_tutor.db.session import get_db, engine
from sangram_tutor.db.init_db import init_db
from sangram_tutor.db.init_vectors import init_vector_db, update_content_embeddings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Sangram Tutor API",
    description="API for the Sangram Tutor AI-powered math learning app",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(learning_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing application...")
    
    # Create directories if they don't exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("vector_indices", exist_ok=True)
    
    # Initialize database with tables and seed data
    db = next(get_db())
    try:
        init_db(db)
        
        # Initialize vector database
        init_vector_db()
        update_content_embeddings(db)
        
        logger.info("Application initialization complete")
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        raise
    finally:
        db.close()

@app.get("/")
async def root():
    """Root endpoint to verify API is running."""
    return {"message": "Sangram Tutor API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

# This is important - it allows the application to be run directly with Python
# or through uvicorn with the module:app syntax
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("sangram_tutor.main:app", host="0.0.0.0", port=8000, reload=True)
