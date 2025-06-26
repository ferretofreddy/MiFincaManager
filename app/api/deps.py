# app/api/deps.py
from typing import Generator, Optional, AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession # Asegúrate de que esto esté importado
import uuid # Necesario para manejar UUIDs

from app import crud, models, schemas # Importa tus módulos
from app.core.config import settings
from app.db.session import async_session_factory # Importa la fábrica de sesiones asíncronas

# Define el esquema de seguridad OAuth2
# Este tokenUrl debe coincidir con la ruta de tu endpoint de login que emite el token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login/access-token")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para obtener una sesión de base de datos asíncrona.
    """
    async with async_session_factory() as session:
        yield session

async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> models.User:
    """
    Dependency para obtener el usuario autenticado a partir de un token JWT.
    """
    try:
        # Decodifica el token usando la clave secreta y el algoritmo configurados
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        # Extrae el ID de usuario del payload. Asegúrate que 'sub' sea el campo correcto
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials - user ID missing.",
            )
        # Convierte el user_id a UUID
        user_id = uuid.UUID(user_id_str)
        # Valida el token con el esquema de usuario (opcional, pero buena práctica)
        token_data = schemas.TokenPayload(sub=user_id_str)
    except (JWTError, ValidationError, ValueError): # Añadido ValueError para errores de UUID
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials - token invalid.",
        )
    
    # Busca al usuario en la base de datos
    user = await crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


async def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    Dependency para obtener el usuario activo y autenticado.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user.")
    return current_user

async def get_current_active_superuser(
    current_user: models.User = Depends(get_current_active_user),
) -> models.User:
    """
    Dependency para obtener el superusuario activo y autenticado.
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
        # Si es superusuario, siempre tiene todos los permisos
        if current_user.is_superuser:
            return current_user

        # Obtener los roles del usuario, cargando sus permisos
        # NOTA: Asegúrate de que crud.user_role.get_roles_for_user cargue la relación 'role'
        # y que el objeto 'role' a su vez cargue la relación 'permissions'.
        # Si no lo hace, necesitarás cargar explícitamente las relaciones aquí o en el CRUD.
        user_roles_associations = await crud.user_role.get_roles_for_user(db, user_id=current_user.id)
        
        # Recargar los roles con sus permisos para asegurar que están cargados
        # Esta parte podría ser optimizada si crud.user_role.get_roles_for_user ya carga
        # permission objects asociados a los roles.
        # Por simplicidad y para asegurar la carga, lo hacemos aquí.
        user_role_ids = [assoc.role_id for assoc in user_roles_associations]
        user_roles_with_permissions = []
        if user_role_ids:
            # Recuperar roles específicos y cargar sus permisos de forma eficiente
            roles_q = await db.execute(
                select(models.Role)
                .filter(models.Role.id.in_(user_role_ids))
                .options(selectinload(models.Role.permissions))
            )
            user_roles_with_permissions = roles_q.scalars().unique().all()


        # Verificar si alguno de los roles del usuario tiene el permiso requerido
        for role in user_roles_with_permissions:
            if role.permissions: # Asegúrate de que 'permissions' es una lista de objetos Permission
                for permission in role.permissions:
                    if permission.name == required_permission_name:
                        return current_user # Usuario tiene el permiso, puede proceder
        
        # Si el bucle termina sin encontrar el permiso, el usuario no está autorizado
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized. Requires permission: '{required_permission_name}'."
        )
    return permission_checker

