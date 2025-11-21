import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import uvicorn
    from shared.config.settings import settings
    
    uvicorn.run(
        "api.main:app",  # ✅ Changed from "main:app" to "api.main:app"
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )