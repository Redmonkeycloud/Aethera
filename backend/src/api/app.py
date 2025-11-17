from fastapi import FastAPI

from .routes import biodiversity, projects, runs


app = FastAPI(title="AETHERA API", version="0.1.0")
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(runs.router, prefix="/runs", tags=["runs"])
app.include_router(biodiversity.router)

