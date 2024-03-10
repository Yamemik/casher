from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import FileResponse

from models.item_model import ItemModel
from services.item_service import create, get_all, get_by_id

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


@item_router.post(
    "/uploads/{file}",
    summary="Скачать файлы",
    status_code=status.HTTP_201_CREATED,
)
async def download_file(file):
    return FileResponse(path=file, filename=file, media_type='multipart/form-data')


@item_router.get(
    "",
    summary="Получить все товары",
    status_code=status.HTTP_200_OK,
)
async def get_items():
    items = get_all()
    return items


@item_router.get(
    "/{item_id}",
    summary="Получить товар ид",
    status_code=status.HTTP_200_OK,
)
async def get_item(item_id):
    item = get_by_id(item_id)
    return item


@item_router.get(
    "/collection/{collection}",
    summary="Получить все товары по коллекции",
    status_code=status.HTTP_200_OK,
)
async def get_items_by_collection(collection):
    items = ...
    return items
