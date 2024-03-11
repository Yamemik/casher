def get_item_serial(item) -> dict:
    return {
        "id": str(item["_id"]),
        "type": str(item["type"]),
        "product": str(item["product"]),
        "images": list(item["images"]),
        "collection": str(item["collection"]),
        "price": int(item["price"]),
        "size_xs": int(item["size_xs"]),
        "size_s": int(item["size_s"]),
        "size_m": int(item["size_m"]),
        "size_l": int(item["size_l"]),
        "size_xl": int(item["size_xl"]),
        "size_xxl": int(item["size_xxl"]),
        "description": str(item["description"]),
        "specifications": dict(item["specifications"]),
        "img_irl": list(item["img_irl"]),
        "is_visible": bool(item["is_visible"]),
        "checker": str(item["checker"]),
    }


def list_items(items) -> list:
    return [get_item_serial(item) for item in items]
