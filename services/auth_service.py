from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from random import randint


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

from schema.user_schema import create_schema
from common.database import user_collection
from schema.user_schema import get_user_serial
from services.user_service import get_user_by_email, get_user_by_email_all, validated_code


SECRET_KEY = "asf5hjjiqvbkpa56"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480000

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict


def reg_user(user_model):
    user_dict = create_schema(dict(user_model))
    user_db = get_user_by_email(user_dict["email"])

    if user_db["email"] is None:
        reg_code = str(randint(1000, 9999))
        send_email(f"Код подтверждения: {reg_code}", user_dict["email"])

        user_dict["password"] = pwd_context.hash(user_dict["password"])
        user_dict["reg_code"] = reg_code
        user_collection.insert_one(user_dict)
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с такой почтой уже зарегистрирован",
            headers={"WWW-Authenticate": "Bearer"},
        )


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
    return Token(access_token=access_token, token_type="bearer", user=user_db)


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


def send_email(text, email):
    msg = MIMEMultipart()
    msg['From'] = "copyright2024@mail.ru"
    msg['To'] = email
    msg['Subject'] = "No replay"
    msg.attach(MIMEText(text, 'plain'))

    smtpObj = smtplib.SMTP('smtp.mail.ru')
    smtpObj.starttls()
    smtpObj.login(msg['From'], 'egAfdRBKbajWYEXTudf7')
    smtpObj.sendmail(msg['From'], msg['To'], msg.as_string())
    smtpObj.quit()
