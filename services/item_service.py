from common.database import item_collection
from schema.item_schema import list_items

from bson import ObjectId

from moysklad_api.client import MoySkladClient


my_storage = MoySkladClient("admin@casher", "casher144", "")


def create(item):
    item_collection.insert_one(dict(item))


def get_all():
    # items = list_items(item_collection.find())
    items = my_storage.get_product_list()
    return items


def get_folders():
    # items = list_items(item_collection.find())
    items = my_storage.get_product_folders()
    return items


def get_by_id(item_id: str):
    return item_collection.find_one({"_id": ObjectId(item_id)})


def get_by_checker(number) -> bool:
    user = item_collection.find_one({"checker": number})
    if user is None:
        return False
    else:
        return True
