from typing import Annotated

from fastapi import APIRouter, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from models.user_model import UserModelCreate
from services.auth_service import reg_user, login_user, reg_user_by_telegram


auth_router = APIRouter(
    prefix="/api/auth",
    tags=["Авторизация"],
)


@auth_router.post(
    "/reg",
    summary="Регистрация",
    status_code=status.HTTP_202_ACCEPTED,
)
async def authenticate_user(user: UserModelCreate):
    if user.email == "":
        reg_user_by_telegram(user)
        access_token = login_user(user.telegram_id, user.password)
        return access_token
    else:
        reg_user(user)
        access_token = login_user(user.email, user.password)
        return access_token


@auth_router.post(
    "/token",
    summary="Авторизация",
    status_code=status.HTTP_202_ACCEPTED
)
async def log_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    access_token = login_user(form_data.username, form_data.password)
    return access_token
