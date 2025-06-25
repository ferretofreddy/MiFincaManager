# app/api/v1/endpoints/users.py
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI (get_db, get_current_user, etc.)
from app.core.security import create_access_token, verify_password, get_password_hash # Importa funciones de seguridad
from app.core.config import settings # Importa la instancia de configuración para variables como ACCESS_TOKEN_EXPIRE_MINUTES

# Importa los CRUDs y Schemas
from app.crud import user as crud_user # Importa la instancia CRUD para usuario
from app import schemas, models # Importa todos los esquemas y modelos


# Asumiendo que 'get_db' y 'get_current_user' estarán en 'app/api/deps.py'
get_db = deps.get_db
get_current_user = deps.get_current_user
get_current_active_user = deps.get_current_active_user # Para usuarios activos
get_current_active_superuser = deps.get_current_active_superuser # Para superusuarios


router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
)

# Endpoint de autenticación (login)
# Este endpoint debería estar en un archivo 'auth.py' o 'login.py' dedicado.
# Lo mantendremos aquí temporalmente para la demostración del usuario, pero se moverá.
@router.post("/login/access-token", response_model=schemas.Token)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth2 login para obtener un token de acceso JWT.
    """
    user = await crud_user.get_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Considera si el usuario está activo antes de emitir un token
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def create_user_account(user_in: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Crea una nueva cuenta de usuario.
    """
    db_user = await crud_user.get_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    
    # Hashear la contraseña antes de pasarla al CRUD
    hashed_password = get_password_hash(user_in.password)
    user_data = user_in.model_dump()
    user_data["password_hash"] = hashed_password # Asigna el hash al campo correcto
    del user_data["password"] # Elimina la contraseña en texto plano

    # Crear una nueva instancia de UserCreate para pasar al CRUD si el esquema lo requiere
    # O simplemente pasar el diccionario de datos
    new_user_create_schema = schemas.UserCreate(**user_data) # Recrea el esquema con el password_hash

    return await crud_user.create(db=db, obj_in=new_user_create_schema)

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
    current_user: models.User = Depends(get_current_active_superuser) # Solo superusuarios pueden leer cualquier usuario por ID
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
    current_user: models.User = Depends(get_current_active_superuser) # Solo superusuarios pueden listar todos los usuarios
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
    # Si el email se está actualizando, verificar que no haya duplicados
    if user_update.email and user_update.email != current_user.email:
        existing_user = await crud_user.get_by_email(db, email=user_update.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered."
            )
    
    # Si se proporciona una nueva contraseña, hashearla
    if user_update.password:
        user_update_data = user_update.model_dump(exclude_unset=True)
        user_update_data["password_hash"] = get_password_hash(user_update.password)
        del user_update_data["password"] # Elimina la contraseña en texto plano
        updated_user = await crud_user.update(db, db_obj=current_user, obj_in=user_update_data)
    else:
        updated_user = await crud_user.update(db, db_obj=current_user, obj_in=user_update)
    
    return updated_user

@router.put("/{user_id}", response_model=schemas.User)
async def update_user_by_id(
    user_id: uuid.UUID,
    user_update: schemas.UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) # Solo superusuarios pueden actualizar cualquier usuario por ID
):
    """
    Actualiza la información de un usuario específico por su ID (solo accesible por superadministradores).
    """
    db_user = await crud_user.get(db, id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Si el email se está actualizando, verificar que no haya duplicados
    if user_update.email and user_update.email != db_user.email:
        existing_user = await crud_user.get_by_email(db, email=user_update.email)
        if existing_user and existing_user.id != db_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered."
            )

    # Si se proporciona una nueva contraseña, hashearla
    if user_update.password:
        user_update_data = user_update.model_dump(exclude_unset=True)
        user_update_data["password_hash"] = get_password_hash(user_update.password)
        del user_update_data["password"]
        updated_user = await crud_user.update(db, db_obj=db_user, obj_in=user_update_data)
    else:
        updated_user = await crud_user.update(db, db_obj=db_user, obj_in=user_update)
    
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_account(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) # Solo superusuarios pueden eliminar usuarios
):
    """
    Elimina una cuenta de usuario por su ID (solo accesible por superadministradores).
    """
    db_user = await crud_user.get(db, id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    await crud_user.remove(db, id=user_id)
    # No devuelve contenido para 204
    return Response(status_code=status.HTTP_204_NO_CONTENT)

