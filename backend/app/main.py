from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.api.v1 import endpoints

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DropRadar API",
    description="High Value Expired Domain & Traffic Interception Radar",
    version="1.0.0"
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
    return {"status": "healthy"}


# Include API routes
app.include_router(endpoints.router, prefix="/api/v1", tags=["domains"])
