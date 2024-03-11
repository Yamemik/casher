from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from schema.user_schema import create_schema
from common.database import user_collection
from services.user_service import get_user_by_email, get_user_by_email_all, get_user_by_tg


SECRET_KEY = "asf5hjjiqvbkpa56"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480000

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


class Token(BaseModel):
    access_token: str
    token_type: str


def reg_user(user_model):
    user_dict = create_schema(dict(user_model))
    user_db = get_user_by_email(user_dict["email"])
    if user_db["email"] is None:
        user_dict["password"] = pwd_context.hash(user_dict["password"])
        user_collection.insert_one(user_dict)
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с такой почтой уже зарегистрирован",
            headers={"WWW-Authenticate": "Bearer"},
        )


def reg_user_by_telegram(user_model):
    user_dict = create_schema(dict(user_model))
    user_db = get_user_by_tg(user_dict["telegram_id"])
    if user_db["telegram_id"] is None:
        user_dict["password"] = pwd_context.hash(user_dict["password"])
        user_collection.insert_one(user_dict)
    else:
        return user_db


def login_user(email, password):
    user_db = get_user_by_email(email)
    access = pwd_context.verify(password, user_db["password"])
    if not access:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверно указан пароль или логин",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user_db["email"]}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_email_all(email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[dict, Depends(get_current_user)]
):
    if current_user["role"] is None:
        raise HTTPException(status_code=400, detail="Не авторизован")
    return current_user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
