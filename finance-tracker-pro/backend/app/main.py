from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.database import engine, Base, get_db
from app.core.config import settings
from app.v1.api import api_router

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI application
app = FastAPI(
    title="Finance Tracker Pro API",
    description="Modern personal finance tracking API with analytics and automation",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Root endpoint - API health check."""
    return {
        "message": "Finance Tracker Pro API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint with database connectivity test."""
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


# Include API router
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
