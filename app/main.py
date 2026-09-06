from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import Base
from app.routers import auth, health, notifications, signals, tracking, watchlist


@asynccontextmanager
async def lifespan(_app: FastAPI):
    from app.db import engine

    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="Watch API",
        description=(
            "Market intelligence backend. Tracking = what already changed. "
            "Signals = what may start to matter before the market fully reacts. "
            "Auth: register/login then send Authorization: Bearer <token>."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if origins == ["*"] else origins,
        allow_credentials=False if origins == ["*"] else True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(health.router)
    application.include_router(auth.router)
    application.include_router(watchlist.router)
    application.include_router(tracking.router)
    application.include_router(signals.router)
    application.include_router(notifications.router)
    return application


app = create_app()
