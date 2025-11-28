import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.v1 import endpoints
from app.core.database import init_db

# Port configuration for Railway
PORT = int(os.getenv("PORT", 8000))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events
    """
    # Startup: Initialize database tables
    print("🚀 Starting DropRadar API...")
    print("📊 Initializing database tables...")
    try:
        init_db()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise
    
    yield
    
    # Shutdown: cleanup if needed
    print("👋 Shutting down DropRadar API...")


app = FastAPI(
    title="DropRadar API",
    description="High Value Expired Domain & Traffic Interception Radar",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "DropRadar API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint that doesn't require database"""
    return {
        "status": "healthy",
        "message": "DropRadar API is running",
        "version": "1.0.0"
    }


# Include API routes
app.include_router(endpoints.router, prefix="/api/v1", tags=["domains"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=PORT,
        reload=False
    )
