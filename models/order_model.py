from pydantic import ConfigDict, BaseModel, Field


class OrderModel(BaseModel):
    user_id: str = Field(...)
    items: list = Field(...)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "user_id": "ид",
                "items": [{
                    "product": "товар",
                    "images": [],
                    "price": 4500,
                    "size": "S",
                },{
                    "product": "товар2",
                    "images": [],
                    "price": 4500,
                    "size": "L",
                },]
            }
        },
    )