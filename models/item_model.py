from pydantic import ConfigDict, BaseModel, Field


class ItemModel(BaseModel):
    type: str = Field(...)
    product: str = Field(...)
    images: list = Field(...)
    collection: str = Field(...)
    price: int = Field(...)
    size_xs: int = Field(default=0)
    size_s: int = Field(default=0)
    size_m: int = Field(default=0)
    size_l: int = Field(default=0)
    size_xl: int = Field(default=0)
    size_xxl: int = Field(default=0)
    description: str = Field(...)
    specifications: dict = Field(...)
    img_irl: list = Field(...)
    is_visible: bool = Field(default=True)
    checker: str = Field(...)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "type": "t-shirt",
                "product": "Джерси money sport red",
                "images": ["img1", "img2", "img3"],
                "collection": "name#1",
                "price": 2800,
                "size_xs": 5,
                "size_s": 5,
                "description": "описание",
                "specifications": {
                    "Состав": "хлопок 90%, полиэстер 10%",
                    "Ткань": "джерси"
                },
                "img_irl": ["img1", "img2", "img3"],
            }
        },
    )