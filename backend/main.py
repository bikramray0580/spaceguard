"""SpaceGuard AI backend application."""

from fastapi import FastAPI

from .api import conjunctions, health, objects, orbits

app = FastAPI(title="SpaceGuard AI Backend", version="0.1.0")

app.include_router(health.router)
app.include_router(objects.router)
app.include_router(orbits.router)
app.include_router(conjunctions.router)
