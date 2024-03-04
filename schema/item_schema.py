def get_item_serial(user) -> dict:
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
    }


def list_items(items) -> list:
    return [get_item_serial(item) for item in items]