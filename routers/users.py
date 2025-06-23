# routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from database import get_db
import schemas
import crud
import models
from app_security import ( # ¡IMPORTANTE: Cambiado de 'security' a 'app_security'!
    create_access_token, 
    verify_password, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from datetime import timedelta
from dependencies import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
)

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para que los usuarios inicien sesión y obtengan un token de acceso JWT.
    """
    user = await crud.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def create_user_account(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Crea una nueva cuenta de usuario.
    """
    db_user = await crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    return await crud.create_user(db=db, user=user)

@router.get("/me/", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    """
    Obtiene la información del usuario actualmente autenticado.
    """
    return current_user

@router.get("/{user_id}", response_model=schemas.User)
async def read_user(
    user_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Requiere autenticación
):
    """
    Obtiene un usuario por su ID.
    """
    # En un entorno de producción, solo un administrador o el propio usuario
    # debería poder acceder a esta información.
    # Por ahora, cualquier usuario autenticado puede leer cualquier usuario por ID.
    # Considera añadir lógica de autorización aquí (ej: if current_user.id != user_id and not current_user.is_admin).
    db_user = await crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/", response_model=list[schemas.User])
async def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Requiere autenticación
):
    """
    Obtiene una lista de usuarios.
    NOTA: En un entorno de producción, esta operación debería estar restringida
    solo a usuarios con permisos de administrador.
    """
    users = await crud.get_users(db, skip=skip, limit=limit)
    return users

@router.put("/{user_id}", response_model=schemas.User)
async def update_user_account(
    user_id: uuid.UUID,
    user_update: schemas.UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Requiere autenticación
):
    """
    Actualiza la información de un usuario.
    Permite a los usuarios actualizar su propia información o a un administrador actualizar cualquier usuario.
    """
    # Solo el propio usuario o un administrador puede actualizar la cuenta
    # Asume que 'is_admin' es un atributo o que hay un rol de administrador.
    # Por simplicidad, aquí solo permitimos que el usuario actualice su propia cuenta.
    if str(user_id) != str(current_user.id):
        # Aquí iría la lógica para verificar si current_user tiene rol de administrador
        # Por ahora, si no es el propio usuario, se prohíbe.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user account."
        )

    db_user = await crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Si el email se está actualizando, verificar que no haya duplicados
    if user_update.email and user_update.email != db_user.email:
        existing_user = await crud.get_user_by_email(db, email=user_update.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered."
            )

    updated_user = await crud.update_user(db, user_id=user_id, user_update=user_update)
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_account(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Requiere autenticación
):
    """
    Elimina una cuenta de usuario.
    Permite a los usuarios eliminar su propia cuenta o a un administrador eliminar cualquier usuario.
    """
    if str(user_id) != str(current_user.id):
        # Lógica de administración para permitir la eliminación de otros usuarios
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user account."
        )

    success = await crud.delete_user(db, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

