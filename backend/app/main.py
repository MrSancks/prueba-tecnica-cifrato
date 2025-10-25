from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer

# Try to load a local .env file if python-dotenv is available. This keeps
# behaviour optional: if the package isn't installed, the app still runs and
# environment variables can be injected by the environment or a process manager.
try:  # pragma: no cover - optional dev-time helper
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=".env")
except Exception:
    # No dotenv available or failed to load; fall back to existing environment.
    pass

from app.presentation import AuthenticationMiddleware, api_router

# Define el esquema de seguridad para Swagger UI
security_scheme = HTTPBearer()


def create_app() -> FastAPI:
    application = FastAPI(
        title="Cifrato Backend",
        # Configura Swagger para mostrar el botón "Authorize"
        swagger_ui_init_oauth={
            "usePkceWithAuthorizationCodeGrant": True,
        },
    )
    application.add_middleware(AuthenticationMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router)
    return application


app = create_app()
