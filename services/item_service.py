from common.database import item_collection
from schema.item_schema import list_items

from bson import ObjectId


def create(item):
    item_collection.insert_one(dict(item))


def get_all():
    items = list_items(item_collection.find_one())
    return items


def get_by_id(item_id: str):
    return item_collection.find_one({"_id": ObjectId(item_id)})
