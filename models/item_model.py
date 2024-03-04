from pydantic import ConfigDict, BaseModel, Field


class ItemModel(BaseModel):
    category: str = Field(...)
    product: str = Field(...)
    images: list = Field(...)
    collection: str = Field(...)
    price: int = Field(...)
    size: list = Field(...)
    description: str = Field(...)
    specifications: dict = Field(...)
    img_irl: list = Field(...)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "category": "Джерси",
                "product": "Джерси money sport red",
                "images": ["img1", "img2", "img3"],
                "collection": "name#1",
                "price": 2800,
                "size": ["S", "M", "L"],
                "description": "описание",
                "specifications": {
                    "Состав": "хлопок 90%, полиэстер 10%",
                    "Ткань": "джерси"
                },
                "img_irl": ["img1", "img2", "img3"],
            }
        },
    )