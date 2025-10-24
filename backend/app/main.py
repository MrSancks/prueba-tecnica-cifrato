from fastapi import FastAPI

from app.presentation import api_router


def create_app() -> FastAPI:
    application = FastAPI(title="Cifrato Backend")
    application.include_router(api_router)
    return application


app = create_app()
