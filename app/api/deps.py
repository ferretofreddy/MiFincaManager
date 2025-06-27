# app/api/deps.py

from typing import Generator, Optional, AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession 
import uuid 

from app import crud, models, schemas 
from app.core.config import settings
from app.db.session import SessionLocal

# Define el esquema de seguridad OAuth2
# Este tokenUrl debe coincidir con la ruta de tu endpoint de login que emite el token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia para obtener una sesión de base de datos asíncrona.
    """
    async with SessionLocal() as session: 
        yield session

async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> models.User:
    """
    Dependencia para obtener el usuario autenticado a partir de un token JWT.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials - user ID missing.",
            )
        user_id = uuid.UUID(user_id_str)
        token_data = schemas.TokenPayload(sub=user_id_str)
    except (JWTError, ValidationError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials - token invalid.",
        )
    
    user = await crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


async def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    Dependencia para obtener el usuario activo y autenticado.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user.")
    return current_user

async def get_current_active_superuser(
    current_user: models.User = Depends(get_current_active_user),
) -> models.User:
    """
    Dependencia para obtener el superusuario activo y autenticado.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="The user doesn't have enough privileges."
        )
    return current_user

def has_permission(required_permission_name: str):
    """
    Dependency factory para verificar si el usuario actual tiene un permiso específico.
    Este validador buscará el permiso en los roles del usuario.
    """
    async def permission_checker(current_user: models.User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
        if current_user.is_superuser:
            return current_user

        user_roles_associations = await crud.user_role.get_roles_for_user(db, user_id=current_user.id)
        
        user_role_ids = [assoc.role_id for assoc in user_roles_associations]
        user_roles_with_permissions = []
        if user_role_ids:
            roles_q = await db.execute(
                select(models.Role)
                .filter(models.Role.id.in_(user_role_ids))
                .options(selectinload(models.Role.permissions))
            )
            user_roles_with_permissions = roles_q.scalars().unique().all()


        for role in user_roles_with_permissions:
            if role.permissions: 
                for permission in role.permissions:
                    if permission.name == required_permission_name:
                        return current_user 
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized. Requires permission: '{required_permission_name}'."
        )
    return permission_checker