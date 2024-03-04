from typing import Annotated
from fastapi import APIRouter, File, UploadFile, status

from models.order_model import OrderModel


order_router = APIRouter(
    prefix="/api/orders",
    tags=["Заказы"]
)


@order_router.post(
    "",
    summary="Создать заказ",
    status_code=status.HTTP_201_CREATED,
)
async def create_order(item: OrderModel):
    pass


@order_router.get(
    "",
    summary="Получить все заказы",
    status_code=status.HTTP_200_OK,
)
async def get_orders():
    items = ...
    return items


@order_router.get(
    "/{user_id}",
    summary="Получить все заказы пользователя",
    status_code=status.HTTP_200_OK,
)
async def get_orders_by_user():
    items = ...
    return items


@order_router.get(
    "/{order_id}",
    summary="Получить заказ ид",
    status_code=status.HTTP_200_OK,
)
async def get_order_by_id():
    item = ...
    return item
