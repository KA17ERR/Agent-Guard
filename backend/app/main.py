"""
AgentGuard backend entrypoint.

Run locally with:
    uvicorn app.main:app --reload --port 8000
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.database import Base, engine
import app.models  # noqa: F401  (ensures all models are registered on Base)

from app.api import agents, llm, regression, scenarios, test_runs, traces

settings = get_settings()

# Configure root logging once, at import time, so every module's
# `logging.getLogger("agentguard.*")` call actually produces output at the
# configured level instead of being silently dropped by Python's default
# "no handlers configured" behavior.
logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("agentguard")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Prototype-grade schema management: create tables if they don't exist.
    # A real deployment would use Alembic migrations instead.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AgentGuard API",
    description="AI Agent Evaluation and Reliability Engine",
    version="0.1.0",
    lifespan=lifespan,
)

# Explicit method/header allow-lists rather than "*": this is a JSON API
# with no cookie-based auth and no custom headers beyond Content-Type, so
# there's no reason to allow anything wider than what's actually used.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/api/health", tags=["health"])
def health_check():
    return {"status": "ok"}


# --- Global error handling -------------------------------------------------
# Keeps error responses consistent JSON shape across the whole API, and
# ensures unexpected exceptions never leak a raw traceback to the client.

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Keeps request-validation errors (bad/missing JSON fields, out-of-range
    # values, etc.) in the same {"error", "status_code"} envelope as every
    # other error response, with the field-level detail preserved under
    # "error" so clients can still tell which field(s) failed.
    logger.info(
        "Validation error on %s %s: %s", request.method, request.url.path, exc.errors()
    )
    return JSONResponse(
        status_code=422,
        # jsonable_encoder because Pydantic v2's error "ctx" can contain
        # non-JSON-serializable values (e.g. the original exception) —
        # encoding defensively here avoids a 500 while trying to report a 422.
        content={"error": jsonable_encoder(exc.errors()), "status_code": 422},
    )


@app.exception_handler(SQLAlchemyError)
async def db_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.exception("Database error while handling %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"error": "A database error occurred.", "status_code": 500},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error while handling %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected error occurred.", "status_code": 500},
    )


app.include_router(agents.router)
app.include_router(llm.router)
app.include_router(scenarios.router)
app.include_router(test_runs.router)
app.include_router(traces.router)
app.include_router(regression.router)
