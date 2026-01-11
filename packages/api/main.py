"""
FastAPI backend for AI Learning Platform

Bridges the pedagogy engine (Python) with the web frontend (Next.js)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path

# Add pedagogy-engine to path
pedagogy_engine_path = Path(__file__).parent.parent / "pedagogy-engine"
sys.path.insert(0, str(pedagogy_engine_path))

from routes import generate, lessons, storyboards

app = FastAPI(
    title="AI Learning Platform API",
    description="API for generating pedagogical content and serving lessons",
    version="0.1.0"
)

# CORS configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(generate.router, prefix="/api/generate", tags=["generation"])
app.include_router(lessons.router, prefix="/api/lessons", tags=["lessons"])
app.include_router(storyboards.router, prefix="/api/storyboard", tags=["storyboards"])


@app.get("/")
async def root():
    return {
        "message": "AI Learning Platform API",
        "version": "0.1.0",
        "endpoints": {
            "generate": "/api/generate",
            "lessons": "/api/lessons",
            "storyboard": "/api/storyboard",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
