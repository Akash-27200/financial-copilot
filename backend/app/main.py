"""FastAPI application entry point."""

import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.logger import logger, request_id_var, generate_request_id
from app.routes import upload, transactions, chat, insights


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("=" * 60)
    logger.info("AI Financial Copilot — Starting up")
    logger.info(f"Model: {get_settings().GROQ_MODEL}")
    logger.info("=" * 60)
    yield
    logger.info("AI Financial Copilot — Shutting down")


app = FastAPI(
    title="AI Financial Copilot",
    description="Upload bank statements and get AI-powered financial insights",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
settings = get_settings()
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log every request with timing and unique request ID."""
    req_id = generate_request_id()
    request_id_var.set(req_id)

    start_time = time.time()
    logger.info(f"→ {request.method} {request.url.path}")

    response = await call_next(request)

    elapsed = round((time.time() - start_time) * 1000, 2)
    logger.info(f"← {request.method} {request.url.path} [{response.status_code}] ({elapsed}ms)")

    response.headers["X-Request-ID"] = req_id
    return response


# Register routes
app.include_router(upload.router, tags=["Upload"])
app.include_router(transactions.router, tags=["Transactions"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(insights.router, tags=["Insights"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "AI Financial Copilot"}
