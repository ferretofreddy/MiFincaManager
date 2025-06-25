# app/api/deps.py
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db # Importa la dependencia get_db
from app.core.config import settings
from app.core.security import decode_access_token
from app.models.user import User # Importa el modelo de usuario
from app import schemas # Importa los esquemas (para TokenPayload)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login/access-token")

async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependencia que verifica el token JWT y retorna el usuario asociado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        if payload is None:
            raise credentials_exception
        token_data = schemas.TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise credentials_exception
    
    # Busca al usuario por el sub (su ID) en la base de datos
    user = await db.execute(select(User).filter(User.id == token_data.sub))
    user = user.scalars().first()
    
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependencia que asegura que el usuario actualmente autenticado esté activo.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependencia que asegura que el usuario actualmente autenticado sea un superadministrador.
    """
    # En tu modelo User, necesitas un campo como 'is_superuser' o un mecanismo de roles
    # para determinar si un usuario es superadministrador.
    # Por ahora, asumiremos un campo 'is_superuser' en el modelo User.
    if not current_user.is_superuser: # Asumiendo un campo is_superuser en el modelo User
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="The user doesn't have enough privileges"
        )
    return current_user

