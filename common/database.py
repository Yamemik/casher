from pymongo import MongoClient

from common.settings import settings


client = MongoClient("mongodb://localhost:27017/casher_database")

db = client["casher_database"]

user_collection = db["users_collection"]
