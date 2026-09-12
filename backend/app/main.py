from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine

# Import models so they're registered on Base.metadata before create_all.
import app.models  # noqa: F401

from app.api import transcript, extraction, mom, projects, templates, documents


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Stage 1/2 MVP: create tables directly rather than requiring
    # Alembic migrations to be run first. Swap for Alembic once the
    # schema stabilizes and multiple environments are in play.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-powered meeting documentation platform "
        "for evidence backed document generation"
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transcript.router, prefix="/api")
app.include_router(extraction.router, prefix="/api")
app.include_router(mom.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(templates.router, prefix="/api")
app.include_router(documents.router, prefix="/api")


@app.get("/api")
def root():
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/api/health")
def health():
    return {"status": "healthy"}