from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings

app = FastAPI(
    title=settings.app_name,
    description="SEAM Backend API",
    version="1.0.0",
)

# Set up CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter()

class HealthCheck(BaseModel):
    status: str
    environment: str

@api_router.get("/health", response_model=HealthCheck)
def health_check():
    """
    Health check endpoint to verify backend status.
    """
    return HealthCheck(status="ok", environment=settings.app_env)

# Include the routers in the main application
app.include_router(api_router, prefix="/api/v1")

from .api import api_router as read_only_router
app.include_router(read_only_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    # Typically, you would run this with: uvicorn backend.main:app --reload
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
