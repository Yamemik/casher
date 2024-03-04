from fastapi import FastAPI
from api.user_route import user_router
from api.auth_route import auth_router

from common.settings import settings


def create_app():
    app = FastAPI(
        debug=settings.debug,
        docs_url="/api/docs",
        title="Casher API docs",
    )

    app.include_router(auth_router)
    app.include_router(user_router)

    return app
