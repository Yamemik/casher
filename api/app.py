from fastapi import FastAPI, Depends
from common.settings import settings

from api.user_route import user_router
from api.auth_route import auth_router
from api.item_route import item_router
from api.order_route import order_router

from services.auth_service import get_current_active_user


def create_app():
    app = FastAPI(
        debug=settings.debug,
        docs_url="/api/docs",
        title="Casher API docs",
    )

    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(item_router, dependencies=[Depends(get_current_active_user)])
    app.include_router(order_router, dependencies=[Depends(get_current_active_user)])

    return app
