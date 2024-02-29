from models import user_model


def reg_serial(user: user_model) -> dict:
    return {
        "id": str(user["_id"]),
        "email": str(user["email"]),
        "password": str(user["password"]),
    }


def get_user_serial(user) -> dict:
    return {
        "id": str(user["_id"]),
        "email": str(user["email"]),
        "telephone_number": str(user["telephone_number"]),
        "city": str(user["city"]),
        "transfer": str(user["transfer"]),
        "point": str(user["point"]),
        "fio": str(user["fio"]),
        "comment": str(user["comment"]),
        "promo_code": str(user["promo_code"]),
        "payment_option": str(user["payment_option"]),
    }


def list_user(users) -> list:
    return [get_user_serial(user) for user in users]
