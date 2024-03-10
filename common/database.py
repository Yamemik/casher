from pymongo import MongoClient


#string_connect = "mongodb+srv://admin:admin@cluster0.532y6ot.mongodb.net/"
string_connect = "mongodb://localhost:27017/casher_database"

client = MongoClient(string_connect)

db = client["casher_database"]

user_collection = db["users_collection"]
item_collection = db["items_collection"]
order_collection = db["order_collection"]





