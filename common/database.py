from pymongo import MongoClient


client = MongoClient("mongodb+srv://admin:admin@cluster0.532y6ot.mongodb.net/")

db = client["casher_database"]

user_collection = db["users_collection"]

