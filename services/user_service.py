from common.database import user_collection
from schema.user_schema import list_user, get_user_serial, get_user_serial_auth
from passlib.context import CryptContext

from bson import ObjectId


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user_by_email(email: str) -> dict:
    user = user_collection.find_one({"email": email})
    if user is None:
        return {
            "id": None,
            "email": None,
            "password": None,
            "role": None,
        }
    return get_user_serial_auth(user)


def get_user_by_id(user_id: str):
    user = get_user_serial(user_collection.find_one({"_id": ObjectId(user_id)}))
    return user


def get_all_users():
    users = list_user(user_collection.find())
    return users


def get_user_by_email_all(email: str) -> dict:
    user = user_collection.find_one({"email": email})
    if user is None:
        return {
            "email": None
        }
    return get_user_serial(user)


def create_owner(password):
    hash_pass: str = pwd_context.hash(password)
    user_collection.insert_one({
        "email": "admin@box.com",
        "password": hash_pass,
        "role": "owner",
    })


def create_employee(email, password, role):
    hash_pass: str = pwd_context.hash(password)
    user_collection.insert_one({
        "email": email,
        "password": hash_pass,
        "role": role,
    })



