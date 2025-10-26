from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import papers

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-powered research paper search platform",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 Starting Research Paper Search API...")
    init_db()
    print("✅ Application ready!")


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Research Paper Search API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/api/v1/papers/health"
    }


# Health check
@app.get("/health")
async def health():
    """General health check"""
    return {"status": "healthy", "service": "api"}


# Include routers
app.include_router(
    papers.router,
    prefix=settings.API_V1_PREFIX,
    tags=["papers"]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )