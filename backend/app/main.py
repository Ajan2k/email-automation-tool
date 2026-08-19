from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import (
    ai_replies,
    analytics,
    auth,
    campaigns,
    companies,
    contacts,
    conversations,
    imports,
    templates,
    tracking,
    webhooks,
)
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import setup_logging
from app.database.base import Base
from app.database.connection import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    # In production use Alembic migrations; create_all keeps local dev simple.
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")] + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}


for router_module in (
    auth,
    contacts,
    companies,
    imports,
    templates,
    campaigns,
    conversations,
    ai_replies,
    analytics,
    tracking,
    webhooks,
):
    app.include_router(router_module.router)
