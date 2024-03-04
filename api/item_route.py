from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status

from models.item_model import ItemModel
from services.item_service import create


item_router = APIRouter(
    prefix="/api/items",
    tags=["Товары"]
)


@item_router.post(
    "",
    summary="Создать товар",
    status_code=status.HTTP_201_CREATED,
)
async def create_item(item: ItemModel):
    create(item)


@item_router.post(
    "/uploads",
    summary="Загрузить файлы",
    status_code=status.HTTP_201_CREATED,
)
async def create_upload_files(
    files: Annotated[
        list[UploadFile], File(description="Multiple files as UploadFile")
    ],
):
    return {"filenames": [file.filename for file in files]}


@item_router.get(
    "",
    summary="Получить все товары",
    status_code=status.HTTP_200_OK,
)
async def get_items():
    items = ...
    return items


@item_router.get(
    "/{category}",
    summary="Получить все товары по категории",
    status_code=status.HTTP_200_OK,
)
async def get_items():
    items = ...
    return items


@item_router.get(
    "/{item_id}",
    summary="Получить товар ид",
    status_code=status.HTTP_200_OK,
)
async def get_items():
    item = ...
    return item
