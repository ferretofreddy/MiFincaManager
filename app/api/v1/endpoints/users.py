# app/api/v1/endpoints/users.py
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response # Importa Response para 204
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

# --- Importaciones de dependencias y seguridad ---
from app.api import deps 
from app.core.security import create_access_token, verify_password, get_password_hash 
from app.core.config import settings 

# Importa los CRUDs y Schemas
from app.crud import user as crud_user 
from app import schemas, models 


# Asumiendo que 'get_db' y 'get_current_user' estarán en 'app/api/deps.py'
get_db = deps.get_db
get_current_user = deps.get_current_user
get_current_active_user = deps.get_current_active_user 
get_current_active_superuser = deps.get_current_active_superuser 


router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def create_user_account(user_in: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Crea una nueva cuenta de usuario.
    """
    db_user = await crud_user.get_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    
    # El crud.user.create ahora maneja el hasheo internamente, así que pasamos user_in directamente
    # sin modificar el campo password_hash aquí. user_in.password contendrá el texto plano
    # gracias a los cambios en schemas/user.py y crud/user.py.
    return await crud_user.create(db=db, obj_in=user_in)

@router.get("/me/", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    """
    Obtiene la información del usuario actualmente autenticado y activo.
    """
    return current_user

@router.get("/{user_id}", response_model=schemas.User)
async def read_user(
    user_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) 
):
    """
    Obtiene un usuario por su ID (solo accesible por superadministradores).
    """
    db_user = await crud_user.get(db, id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/", response_model=list[schemas.User])
async def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) 
):
    """
    Obtiene una lista de usuarios (solo accesible por superadministradores).
    """
    users = await crud_user.get_multi(db, skip=skip, limit=limit)
    return users

@router.put("/me/", response_model=schemas.User)
async def update_current_user(
    user_update: schemas.UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Actualiza la información del usuario actualmente autenticado.
    """
    if user_update.email and user_update.email != current_user.email:
        existing_user = await crud_user.get_by_email(db, email=user_update.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered."
            )
    
    # === CORRECCIÓN AQUÍ: user_update.password_hash no existe en el esquema Update ===
    # El CRUD se encarga de hashear si se pasa 'password'
    updated_user = await crud_user.update(db, db_obj=current_user, obj_in=user_update)
    
    return updated_user

@router.put("/{user_id}", response_model=schemas.User)
async def update_user_by_id(
    user_id: uuid.UUID,
    user_update: schemas.UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) 
):
    """
    Actualiza la información de un usuario específico por su ID (solo accesible por superadministradores).
    """
    db_user = await crud_user.get(db, id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_update.email and user_update.email != db_user.email:
        existing_user = await crud_user.get_by_email(db, email=user_update.email)
        if existing_user and existing_user.id != db_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered."
            )

    # === CORRECCIÓN AQUÍ: user_update.password_hash no existe en el esquema Update ===
    # El CRUD se encarga de hashear si se pasa 'password'
    updated_user = await crud_user.update(db, db_obj=db_user, obj_in=user_update)
    
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_account(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) 
):
    """
    Elimina una cuenta de usuario por su ID (solo accesible por superadministradores).
    """
    db_user = await crud_user.get(db, id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    await crud_user.remove(db, id=user_id)
    # === ¡CORRECCIÓN CLAVE AQUÍ! No retornar nada para 204 No Content ===
    return 