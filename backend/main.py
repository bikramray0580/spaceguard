"""SpaceGuard FastAPI application.

Thin HTTP integration over the repository's main data-ingestion,
SGP4 propagation, conjunction, uncertainty, and risk modules.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import health, objects, orbits, conjunctions, maneuver

app = FastAPI(title="SpaceGuard AI Backend", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(objects.router)
app.include_router(orbits.router)
app.include_router(conjunctions.router)
app.include_router(maneuver.router)
