# app/api/v1/endpoints/roles.py
from fastapi import APIRouter, Depends, HTTPException, status, Response # Importa Response
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List

# --- Importaciones de módulos centrales ---
from app import schemas, models
from app.crud import role as crud_role # Importa la instancia CRUD para role


# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI

# Asumiendo que 'get_db' y 'get_current_active_user' etc. estarán en 'app/api/deps.py'
get_db = deps.get_db
get_current_active_user = deps.get_current_active_user
get_current_active_superuser = deps.get_current_active_superuser # Para superusuarios


router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Role, status_code=status.HTTP_201_CREATED)
async def create_new_role(
    role_in: schemas.RoleCreate, # Renombrado
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) # Solo superusuarios pueden crear roles
):
    """
    Crea un nuevo rol.
    Requiere autenticación de superusuario.
    """
    db_role = await crud_role.get_by_name(db, name=role_in.name) # Usar crud_role
    if db_role:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Role with this name already exists"
        )
    return await crud_role.create(db=db, obj_in=role_in) # Usar crud_role

@router.get("/{role_id}", response_model=schemas.Role)
async def read_role(
    role_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user) # Cualquier usuario activo puede leer roles
):
    """
    Obtiene un rol por su ID.
    """
    db_role = await crud_role.get(db, id=role_id) # Usar crud_role
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.get("/", response_model=List[schemas.Role])
async def read_roles(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user) # Cualquier usuario activo puede leer roles
):
    """
    Obtiene una lista de roles.
    """
    roles = await crud_role.get_multi(db, skip=skip, limit=limit) # Usar crud_role
    return roles

@router.put("/{role_id}", response_model=schemas.Role)
async def update_existing_role(
    role_id: uuid.UUID,
    role_update: schemas.RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) # Solo superusuarios pueden actualizar roles
):
    """
    Actualiza un rol existente por su ID.
    Requiere autenticación de superusuario.
    """
    db_role = await crud_role.get(db, id=role_id) # Usar crud_role
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Verificar si el nuevo nombre ya existe si se está actualizando el nombre
    if role_update.name and role_update.name != db_role.name:
        existing_role_with_name = await crud_role.get_by_name(db, name=role_update.name) # Usar crud_role
        if existing_role_with_name and existing_role_with_name.id != role_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Role with this name already exists."
            )

    updated_role = await crud_role.update(db, db_obj=db_role, obj_in=role_update) # Usar crud_role
    return updated_role

@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_role(
    role_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) # Solo superusuarios pueden eliminar roles
):
    """
    Elimina un rol por su ID.
    Requiere autenticación de superusuario.
    """
    db_role = await crud_role.get(db, id=role_id)
    if not db_role: # Verificar que el rol exista antes de intentar eliminarlo
        raise HTTPException(status_code=404, detail="Role not found")

    deleted_role = await crud_role.remove(db, id=role_id) # Usar crud_role
    if not deleted_role:
        raise HTTPException(status_code=404, detail="Role not found or could not be deleted")
    return Response(status_code=status.HTTP_204_NO_CONTENT) # Retorno correcto para 204

