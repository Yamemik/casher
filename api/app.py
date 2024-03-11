from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
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

    app.mount("/static", StaticFiles(directory="static"), name="static")

    origins = [
        "https://cashercollection.com/",
        "https://cashercollection.shop/",
        "http://localhost",
        "http://localhost:3000",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(item_router, dependencies=[Depends(get_current_active_user)])
    app.include_router(order_router, dependencies=[Depends(get_current_active_user)])

    return app
