from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.middleware import InMemoryRateLimitMiddleware, SecurityHeadersMiddleware


def validate_production_settings() -> None:
    """Fail fast before importing heavyweight API routers in unsafe production config."""
    if settings.environment.lower() == "production" and settings.jwt_secret_key == "change-this-before-production":
        raise RuntimeError("JWT_SECRET_KEY must be replaced before production startup.")
    if settings.environment.lower() == "production" and (
        settings.demo_ceo_password == "nexusmind-demo" or settings.demo_admin_password == "nexusmind-demo"
    ):
        raise RuntimeError("Demo user passwords must be replaced before production startup.")


def create_app() -> FastAPI:
    validate_production_settings()
    from app.api.v1.router import api_router

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Autonomous Enterprise Intelligence and Digital Twin Platform",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(InMemoryRateLimitMiddleware)

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["system"])
    def health_check() -> dict[str, str]:
        return {"status": "operational", "system": settings.app_name}

    return app


app = create_app()
