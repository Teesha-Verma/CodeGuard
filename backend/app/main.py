import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as review_router
from app.core.logger import get_logger
from app.core.config import get_settings
from app.db.database import engine, Base


settings = get_settings()
logger = get_logger("codeguard.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize database tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade hybrid static-analysis + LLM reasoning code review engine.",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    
    logger.info(
        f"Handled {request.method} {request.url.path}",
        extra={
            "duration_ms": duration_ms,
            "status_code": response.status_code,
            "method": request.method,
            "path": request.url.path
        }
    )
    return response

from fastapi.responses import JSONResponse
from app.core.logger import mask_secrets

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    sanitized_msg = mask_secrets(str(exc))
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {sanitized_msg}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred."}
    )

app.include_router(review_router)

@app.get("/health", tags=["System"])
def health_check():
    groq_configured = bool(
        settings.GROQ_API_KEY and settings.GROQ_API_KEY not in ("mock_key", "your_groq_api_key_here")
    )
    gemini_configured = bool(
        settings.GEMINI_API_KEY and settings.GEMINI_API_KEY not in ("mock_key", "your_gemini_api_key_here")
    )
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm": {
            "primary_provider": settings.LLM_PROVIDER,
            "fallback_providers": settings.fallback_provider_list,
            "groq_configured": groq_configured,
            "gemini_llm_configured": gemini_configured,
            "gemini_embeddings_configured": gemini_configured,
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
