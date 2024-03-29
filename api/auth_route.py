from typing import Annotated

from fastapi import APIRouter, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from models.user_model import UserModelCreate
from services.auth_service import reg_user, login_user, validated_code


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
    reg_user(user)
    access_token = login_user(user.email, user.password)
    return access_token


@auth_router.post(
    "/reg/validated",
    summary="Подтверждение почты",
    status_code=status.HTTP_202_ACCEPTED,
)
async def validated_email(code: str):
    return validated_code(code)


@auth_router.post(
    "/token",
    summary="Авторизация",
    status_code=status.HTTP_202_ACCEPTED
)
async def log_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    access_token = login_user(form_data.username, form_data.password)
    return access_token
