from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
from typing import Any

from app.config import settings
from app.database import get_db
from app.models import User
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, stored_hash: str) -> bool:
    return pwd_context.verify(password, stored_hash)

def create_access_token(data: dict[str, Any]) -> str:
    data_copy = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    data_copy['exp'] = expire

    token = jwt.encode(data_copy, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_error = HTTPException(status_code=401, detail='Could not validate credentials')

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        raise credentials_error

    user_id = payload.get('sub')
    if user_id is None:
        raise credentials_error

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_error

    return user

def require_role(required_role: str):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return current_user
    return role_checker
