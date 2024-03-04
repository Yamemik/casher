from common.database import item_collection
from schema.item_schema import list_items


def create(item):
    item_collection.insert_one(item)