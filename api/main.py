"""
FastAPI application — main entry point.
Serves the API and the frontend SPA.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from monitoring.logger import get_logger
from api.routes.claims import router as claims_router
from api.routes.auth import router as auth_router
from api.schemas import HealthResponse

log = get_logger("api.main")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

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
# Include the auth router under /api prefix
app.include_router(auth_router, prefix="/api", tags=["Auth"])

# Mount static files (CSS, JS, images) from the frontend directory
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Simple health check endpoint to verify API availability.
    """
    return HealthResponse(status="healthy", version="1.0.0")


@app.get("/", tags=["Frontend"])
async def serve_frontend():
    """
    Serve the main SPA index.html for the root URL.
    """
    return FileResponse(str(FRONTEND_DIR / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
