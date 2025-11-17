from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from .routes import biodiversity, countries, projects, runs


app = FastAPI(title="AETHERA API", version="0.1.0")

# Add CORS middleware to allow frontend to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - redirects to API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "service": "AETHERA API",
        "version": "0.1.0"
    })


app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(runs.router, prefix="/runs", tags=["runs"])
app.include_router(biodiversity.router)
app.include_router(countries.router)

