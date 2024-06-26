from common.database import user_collection
from schema.user_schema import list_user, get_user_serial, get_user_serial_auth
from passlib.context import CryptContext

from bson import ObjectId
from pymongo import ReturnDocument


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user_by_email(email: str) -> dict:
    user = user_collection.find_one({"email": email})
    if user is None:
        return {
            "id": None,
            "email": None,
            "password": None,
            "telegram_id": None,
            "role": None,
        }
    else:
        return get_user_serial_auth(user)


def get_user_by_tg(telegram_id: str) -> dict:
    user = user_collection.find_one({"telegram_id": telegram_id})
    if user is None:
        return {
            "id": None,
            "email": None,
            "password": None,
            "telegram_id": None,
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
    user = user_collection.find_one({"role": "owner"})
    if user is None:
        user_collection.insert_one({
            "email": "owner@email.ru",
            "telegram_id": "",
            "password": hash_pass,
            "role": "owner",
            "telephone_number": "",
            "city": "",
            "transfer": "",
            "point": "",
            "fio": "",
            "comment": "",
            "promo_code": "",
            "payment_option": "",
        })


def create_employee(email, password, role, fio):
    hash_pass: str = pwd_context.hash(password)
    user_collection.insert_one({
        "email": email,
        "telegram_id": "",
        "password": hash_pass,
        "role": role,
        "telephone_number": "",
        "city": "",
        "transfer": "",
        "point": "",
        "fio": fio,
        "comment": "",
        "promo_code": "",
        "payment_option": "",
    })


def validated_code(code: str):
    user_db = user_collection.find_one_and_update(
        {"reg_code": code, "is_validated": False},
        {'$set': {"is_validated": True}},
        return_document=ReturnDocument.AFTER
    )
    return get_user_serial(user_db)

