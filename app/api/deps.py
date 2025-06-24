# app/api/deps.py
from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession # Asegúrate de que esto sea AsyncSession

from app.db.session import AsyncSessionLocal # Importa tu sesión de base de datos
from app.core.config import settings # Importa tus configuraciones
from app.core import security # Importa tu módulo de seguridad
from app import crud, schemas # Importa crud y schemas para validar el usuario

# OAuth2PasswordBearer es una dependencia de FastAPI para obtener el token del header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/login/access-token")

async def get_db() -> Generator:
    """
    Dependency to get a database session.
    """
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> schemas.User: # Asumiendo que schemas.User es tu esquema de usuario completo
    """
    Dependency to get the current authenticated user from the JWT token.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials (username missing)",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = schemas.TokenData(username=username) # Usa tu esquema TokenData
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials (token invalid)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await crud.user_crud.get_by_email(db, email=token_data.username) # Asegúrate que crud.user_crud.get_by_email existe y funciona con AsyncSession
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user

async def get_current_active_user(
    current_user: schemas.User = Depends(get_current_user),
) -> schemas.User:
    """
    Dependency to get the current active authenticated user.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

async def get_current_active_superuser(
    current_user: schemas.User = Depends(get_current_active_user),
) -> schemas.User:
    """
    Dependency to get the current active authenticated superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="The user doesn't have enough privileges"
        )
    return current_user
