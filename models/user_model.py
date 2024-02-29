from pydantic import ConfigDict, BaseModel, Field, EmailStr
from typing import Optional
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated


PyObjectId = Annotated[str, BeforeValidator(str)]


class UserModel(BaseModel):
    """
    Container for a single user record.
    """

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    email: EmailStr = Field(...)
    telephone_number: str = Field(...)
    city: str = Field(...)
    transfer: str = Field(...)
    point: str = Field(...)
    fio: str = Field(...)
    comment: str = Field(...)
    promo_code: str = Field(...)
    payment_option: str = Field(...)
    password: str = Field(...)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "email": "jdoe@example.com",
                "telephone_number": "+79997775566",
                "city": "Город",
                "transfer": "cdek",
                "point": "пункт получения",
                "fio": "фио",
                "comment": "комментарий",
                "promo_code": "промокод",
                "payment_option": "способ оплаты",
            }
        },
    )
