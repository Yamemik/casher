def create_schema(user) -> dict:
    return {
        "email": str(user["email"]),
        "password": str(user["password"]),
        "telegram_id": str(user["telegram_id"]),
        "reg_code": str(user["reg_code"]),
        "role": str(user["role"]),
        "is_validated": bool(user["is_validated"]),
        "telephone_number": "",
        "city": "",
        "transfer": "",
        "point": "",
        "fio": "",
        "comment": "",
        "promo_code": "",
        "payment_option": "",
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
        "role": str(user["role"]),
        "is_validated": str(user["is_validated"]),
    }


def list_user(users) -> list:
    return [get_user_serial(user) for user in users]


def get_user_serial_auth(user) -> dict:
    return {
        "id": str(user["_id"]),
        "email": str(user["email"]),
        "telegram_id": str(user["telegram_id"]),
        "password": str(user["password"]),
        "role": str(user["role"]),
        "is_validated": str(user["is_validated"]),
    }
