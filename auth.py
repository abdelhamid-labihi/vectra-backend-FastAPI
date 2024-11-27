from datetime import datetime
import json
from fastapi import Depends, HTTPException, Response, status
from jose import jwt, JWTError
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from lib import (
    MagicNumberBody,
    UserLogin,
    UserSignup,
    create_user,
    get_user,
    is_user_email_duplicate,
)
from magic_link import (
    confirm_user,
    generate_magic_number,
    save_magic_number,
    verify_magic_number,
)
from orm import MAGIC_LINK_EXPIRY, User, TZ, db
from fastapi.security import OAuth2PasswordBearer

from send_magic_email import send_email_with_magic_number

load_dotenv()


SECRET_KEY: str = os.getenv("SECRET_KEY", "")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict):
    expire = datetime.now(TZ) + MAGIC_LINK_EXPIRY
    data.update({"exp": expire})
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_current_user(response: Response, token: str = Depends(oauth2_scheme)):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_access_token(token)
    if payload is None:
        raise credentials_exception

    if datetime.fromtimestamp(payload["exp"], TZ) < datetime.now(TZ):
        raise credentials_exception

    user = db.query(User).filter_by(id=payload["sub"]).first()
    if user is None:
        raise credentials_exception

    new_token = create_access_token(data={"sub": user.email})
    response.headers["Authorization"] = f"Bearer {new_token}"

    return json.dumps(user.to_dict())


async def sign_up(user_info: UserSignup):
    if is_user_email_duplicate(user_info.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    new_user = create_user(user_info)
    magic_number = generate_magic_number()
    save_magic_number(new_user, magic_number)
    send_email_with_magic_number(new_user, magic_number)
    return status.HTTP_200_OK


async def login(user_info: UserLogin):
    user = get_user(user_info.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The email you entered is incorrect.",
        )
    magic_number = generate_magic_number()
    save_magic_number(user, magic_number)
    send_email_with_magic_number(user, magic_number)
    return status.HTTP_200_OK


async def validate_magic_number(response: Response, magic_number: MagicNumberBody):
    if not await verify_magic_number(magic_number.magic_number):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The code you entered is incorrect or has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email = await confirm_user(magic_number.magic_number)
    access_token = create_access_token(data={"sub": email})
    response.headers["Authorization"] = f"Bearer {access_token}"
    return status.HTTP_200_OK
