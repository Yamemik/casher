from fastapi import FastAPI
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from api.user_route import router

from common.settings import settings


def create_app():
    app = FastAPI(
        debug=settings.debug,
        docs_url="/api/docs",
        title="Casher API docs",
    )

    app.include_router(router)

    return app
