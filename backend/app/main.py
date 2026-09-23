"""Main FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config import settings
from app.database import get_db, Base, engine
from app.api import api_router
from app.agent.ollama_client import ollama_client
from app.utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event to verify database on startup."""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info(f"CertAgen backend ready on {settings.HOST}:{settings.PORT}")
    yield
    logger.info("CertAgen backend shutting down.")

app = FastAPI(
    title="CertAgen — Enterprise Certificate AI Operations Agent",
    description="Operational AI Agent with local Ollama tool calling for enterprise certificate lifecycle management.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", summary="Health check endpoint")
async def health_check(db: Session = Depends(get_db)):
    """Health check verifying local Ollama instance and database connectivity."""
    db_status = "available"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unavailable"

    ollama_info = await ollama_client.check_health()
    ollama_status = "available" if ollama_info.get("available") else "unavailable"

    overall_status = "ok" if (db_status == "available" and ollama_status == "available") else "degraded"

    return {
        "status": overall_status,
        "ollama": ollama_status,
        "database": db_status,
        "model": settings.OLLAMA_MODEL,
        "details": {
            "model_ready": ollama_info.get("model_ready", False),
            "ollama_info": ollama_info.get("status"),
        }
    }

# Mount /api routes
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
