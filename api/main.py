from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from shared.config.settings import settings
from api.routes import auth, simulations, users
import logging
from api.routes import keyvault, password_checker, secret_scanner


# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🚀 Starting CyberSec Platform API...")
    logger.info(f"📊 MongoDB URI: {settings.MONGODB_URI[:50]}...")
    logger.info(f"🗄️  Database Name: {settings.DATABASE_NAME}")
    
    app.mongodb_client = AsyncIOMotorClient(settings.MONGODB_URI)
    app.mongodb = app.mongodb_client[settings.DATABASE_NAME]
    
    logger.info(f"🔍 Database object type: {type(app.mongodb)}")
    logger.info(f"🔍 Database name: {app.mongodb.name}")
    
    try:
        await app.mongodb_client.admin.command('ping')
        logger.info(f"✅ Successfully connected to MongoDB Atlas")
        logger.info(f"✅ Database: {settings.DATABASE_NAME}")
        
        # List collections
        collections = await app.mongodb.list_collection_names()
        logger.info(f"📋 Collections in database: {collections}")
        
        # Check users collection
        if "users" in collections:
            users_count = await app.mongodb["users"].count_documents({})
            logger.info(f"👥 Users in collection: {users_count}")
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {str(e)}")
        raise
    
    yield
    
    app.mongodb_client.close()
    logger.info("🛑 MongoDB connection closed")

app = FastAPI(
    title="CyberSec Platform API",
    description="Secure authentication and cybersecurity simulation platform with RBAC",
    version="2.0.0",
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
    
    # DEBUG: Log every request
    logger.debug(f"📨 {request.method} {request.url.path}")
    logger.debug(f"🗄️  DB in request: {request.state.db.name}")
    
    response = await call_next(request)
    return response

def get_db(request: Request):
    """Dependency to get database"""
    return request.state.db

app.dependency_overrides[AsyncIOMotorClient] = get_db

# Include routers
app.include_router(auth.router)
app.include_router(simulations.router)
app.include_router(users.router)

@app.get("/")
async def root():
    return {
        "message": "CyberSec Platform API with RBAC",
        "version": "2.0.0",
        "status": "operational",
        "features": ["Authentication", "MFA", "RBAC", "File Encryption", "Email Delivery"],
        "database": settings.DATABASE_NAME
    }

@app.get("/health")
async def health_check():
    try:
        await app.mongodb_client.admin.command('ping')
        
        # Count users
        users_count = await app.mongodb["users"].count_documents({})
        
        return {
            "status": "healthy",
            "database": "connected",
            "database_name": settings.DATABASE_NAME,
            "users_count": users_count,
            "rbac": "enabled"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

@app.get("/debug/users")
async def debug_users():
    """DEBUG ENDPOINT - Remove in production!"""
    try:
        users = await app.mongodb["users"].find({}).to_list(length=10)
        return {
            "count": len(users),
            "users": [
                {
                    "email": u.get("email"),
                    "role": u.get("role"),
                    "active": u.get("is_active"),
                    "verified": u.get("is_verified")
                }
                for u in users
            ]
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting server with uvicorn...")
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level="info"
    )

app.include_router(keyvault.router)
app.include_router(password_checker.router)
app.include_router(secret_scanner.router)