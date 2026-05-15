"""
FastAPI application — main entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from monitoring.logger import get_logger
from api.routes.claims import router as claims_router
from api.schemas import HealthResponse

log = get_logger("api.main")

# Initialize the main FastAPI application instance with metadata
app = FastAPI(
    title="Health Claims Denial Prevention API",
    version="1.0.0",
    description="AI-powered system to predict claim denials, explain reasons, and suggest fixes.",
)

# Add CORS middleware to allow cross-origin requests (e.g. from frontend dashboard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the claims router to expose endpoints under the /api prefix
app.include_router(claims_router, prefix="/api", tags=["Claims"])


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Simple health check endpoint to verify API availability.
    """
    return HealthResponse(status="healthy", version="1.0.0")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
