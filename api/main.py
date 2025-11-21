from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from shared.config.settings import settings
from api.routes import auth, simulations
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    app.mongodb_client = AsyncIOMotorClient(settings.MONGODB_URI)
    app.mongodb = app.mongodb_client[settings.DATABASE_NAME]
    
    try:
        await app.mongodb_client.admin.command('ping')
        logger.info("Successfully connected to MongoDB Atlas")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise
    
    yield
    
    app.mongodb_client.close()
    logger.info("MongoDB connection closed")

app = FastAPI(
    title="CyberSec Platform API",
    description="Secure authentication and cybersecurity simulation platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_db_to_request(request: Request, call_next):
    """Add database to request state"""
    request.state.db = app.mongodb
    response = await call_next(request)
    return response

def get_db(request: Request):
    """Dependency to get database"""
    return request.state.db

app.dependency_overrides[AsyncIOMotorClient] = get_db

app.include_router(auth.router)
app.include_router(simulations.router)

@app.get("/")
async def root():
    return {
        "message": "CyberSec Platform API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    try:
        await app.mongodb_client.admin.command('ping')
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )