from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title = settings.APP_NAME,
    version = settings.APP_VERSION,
    description =(
        "AI-powered meeting documentation platform"
        "for evidence backed document generation"
    ),
)

@app.get('/')
def root():
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
    }