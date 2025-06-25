# app/api/v1/endpoints/permissions.py
from fastapi import APIRouter, Depends, HTTPException, status, Response # Importa Response
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Optional

# --- Importaciones de módulos centrales ---
from app import schemas, models
from app.crud import permission as crud_permission # Importa la instancia CRUD para permission
from app.crud import module as crud_module # Importa la instancia CRUD para module


# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI

# Asumiendo que 'get_db' y 'get_current_active_user' etc. estarán en 'app/api/deps.py'
get_db = deps.get_db
get_current_active_user = deps.get_current_active_user
get_current_active_superuser = deps.get_current_active_superuser # Para superusuarios


router = APIRouter(
    prefix="/permissions",
    tags=["Permissions"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Permission, status_code=status.HTTP_201_CREATED)
async def create_new_permission(
    permission_in: schemas.PermissionCreate, # Renombrado
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) # Solo superusuarios pueden crear permisos
):
    """
    Crea un nuevo permiso.
    Requiere autenticación de superusuario.
    """
    db_permission = await crud_permission.get_by_name(db, name=permission_in.name) # Usar crud_permission
    if db_permission:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Permission with this name already exists"
        )
    
    # Verificar si el module_id proporcionado existe si se especifica
    if permission_in.module_id:
        db_module = await crud_module.get(db, id=permission_in.module_id) # Usar crud_module
        if not db_module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module not found."
            )

    return await crud_permission.create(db=db, obj_in=permission_in) # Usar crud_permission

@router.get("/{permission_id}", response_model=schemas.Permission)
async def read_permission(
    permission_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user) # Cualquier usuario activo puede leer permisos
):
    """
    Obtiene un permiso por su ID.
    """
    db_permission = await crud_permission.get(db, id=permission_id) # Usar crud_permission
    if db_permission is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    return db_permission

@router.get("/", response_model=List[schemas.Permission])
async def read_permissions(
    skip: int = 0, 
    limit: int = 100, 
    module_id: Optional[uuid.UUID] = None, # Filtro opcional por module_id
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user) # Cualquier usuario activo puede leer permisos
):
    """
    Obtiene una lista de permisos, opcionalmente filtrada por ID de módulo.
    """
    if module_id:
        permissions = await crud_permission.get_multi_by_module(db, module_id=module_id, skip=skip, limit=limit) # Usar crud_permission
    else:
        permissions = await crud_permission.get_multi(db, skip=skip, limit=limit) # Usar crud_permission
    return permissions

@router.put("/{permission_id}", response_model=schemas.Permission)
async def update_existing_permission(
    permission_id: uuid.UUID,
    permission_update: schemas.PermissionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) # Solo superusuarios pueden actualizar permisos
):
    """
    Actualiza un permiso existente por su ID.
    Requiere autenticación de superusuario.
    """
    db_permission = await crud_permission.get(db, id=permission_id) # Usar crud_permission
    if db_permission is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    # Opcional: Verificar si el nuevo nombre ya existe si se está actualizando el nombre
    if permission_update.name and permission_update.name != db_permission.name:
        existing_permission_with_name = await crud_permission.get_by_name(db, name=permission_update.name) # Usar crud_permission
        if existing_permission_with_name and existing_permission_with_name.id != permission_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Permission with this name already exists."
            )

    # Si se intenta cambiar el module_id, verificar el nuevo módulo
    if permission_update.module_id is not None and permission_update.module_id != db_permission.module_id:
        new_module = await crud_module.get(db, id=permission_update.module_id) # Usar crud_module
        if not new_module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="New module for permission update not found."
            )

    updated_permission = await crud_permission.update(db, db_obj=db_permission, obj_in=permission_update) # Usar crud_permission
    return updated_permission

@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_permission(
    permission_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) # Solo superusuarios pueden eliminar permisos
):
    """
    Elimina un permiso por su ID.
    Requiere autenticación de superusuario.
    """
    db_permission = await crud_permission.get(db, id=permission_id)
    if not db_permission: # Verificar que el permiso exista antes de intentar eliminarlo
        raise HTTPException(status_code=404, detail="Permission not found")
        
    deleted_permission = await crud_permission.remove(db, id=permission_id) # Usar crud_permission
    if not deleted_permission:
        raise HTTPException(status_code=404, detail="Permission not found or could not be deleted")
    return Response(status_code=status.HTTP_204_NO_CONTENT) # Retorno correcto para 204

