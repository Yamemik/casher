from pydantic import ConfigDict, BaseModel, Field, EmailStr


class UserModelCreate(BaseModel):
    """
    Container for a single user record.
    """

    email: str = Field(...)
    telegram_id: str = Field(...)
    password: str = Field(...)
    role: str = Field(default="user")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "email": "kuancarlos@mail.ru",
                "telegram_id": "",
                "password": "123",

            }
        },
    )


class UserModelUpdate(BaseModel):
    telephone_number: str = Field(...)
    city: str = Field(...)
    transfer: str = Field(...)
    point: str = Field(...)
    fio: str = Field(...)
    comment: str = Field(...)
    promo_code: str = Field(...)
    payment_option: str = Field(...)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "email": "kuancarlos@mail.ru",
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
