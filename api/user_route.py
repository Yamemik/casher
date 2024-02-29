from fastapi import APIRouter
from models import user_model
from schema.user_schema import list_user
from common.database import user_collection

from bson import ObjectId


router = APIRouter(
    prefix="/api/users",
    tags=["Пользователи"],
)


@router.get(
    "",
    summary="Получить всех пользователей",
    response_description="Список всех пользователей",
    response_model_by_alias=False,
)
async def get_users():
    users = list_user(user_collection.find())
    return users
