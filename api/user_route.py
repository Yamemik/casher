from typing import Annotated
from fastapi import APIRouter, status, Depends, HTTPException

from models.user_model import UserModelUpdate
from services.user_service import get_all_users, get_user_by_id, create_owner, create_employee
from services.auth_service import get_current_active_user


user_router = APIRouter(
    prefix="/api/users",
    tags=["Пользователи"],
)


@user_router.post(
    "",
    summary="Создать пользователя",
    response_description="Созданный пользователь",
    status_code=status.HTTP_201_CREATED,
)
async def post_user(user: UserModelUpdate, current_user: Annotated[UserModelUpdate, Depends(get_current_active_user)]):
    if current_user["role"] != "owner":
        raise HTTPException(status_code=400, detail="Недостаточно прав")
    pass


@user_router.get(
    "",
    summary="Получить всех пользователей",
)
async def get_users(current_user: Annotated[UserModelUpdate, Depends(get_current_active_user)]):
    users = get_all_users()
    return users


@user_router.get(
    "/me",
    summary="Получить пользователя по токену",
)
async def read_users_me(current_user: Annotated[UserModelUpdate, Depends(get_current_active_user)]):
    return current_user


@user_router.get(
    "/{user_id}",
    summary="Получить пользователя по ид",
)
async def get_user(user_id, current_user: Annotated[UserModelUpdate, Depends(get_current_active_user)]):
    user = get_user_by_id(user_id)
    return user


@user_router.patch(
    "",
    summary="Обновить пользователя",
    response_description="Обновленный пользователь",
    response_model=UserModelUpdate,
    status_code=status.HTTP_202_ACCEPTED,
    response_model_by_alias=False,
)
async def patch_user(user: UserModelUpdate,
                     current_user: Annotated[UserModelUpdate, Depends(get_current_active_user)]):
    pass


@user_router.post(
    "/create_owner",
    summary="Создать владельца",
    status_code=status.HTTP_201_CREATED,
)
async def post_create_owner(password: str):
    create_owner(password)


@user_router.post(
    "/create_employee",
    summary="Создать сотрудника",
    status_code=status.HTTP_201_CREATED,
)
async def post_create_employee(email: str, password: str, role: str, fio: str,
                               current_user: Annotated[UserModelUpdate, Depends(get_current_active_user)]):
    if current_user["role"] == "admin" or current_user["role"] == "owner":
        if role == "redactor" or role == "admin":
            create_employee(email, password, role, fio)
        else:
            raise HTTPException(status_code=400, detail="Неверно введена роль (redactor or admin)")
    else:
        raise HTTPException(status_code=400, detail="Недостаточно прав")
