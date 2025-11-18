from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import biodiversity, layers, projects, runs, tasks


app = FastAPI(title="AETHERA API", version="0.1.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "AETHERA API",
        "version": "0.1.0",
        "docs": "/docs",
    }


app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(runs.router, prefix="/runs", tags=["runs"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(biodiversity.router)
app.include_router(layers.router)

