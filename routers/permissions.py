# routers/permissions.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Optional

from database import get_db
import schemas
import crud
import models
from dependencies import get_current_user

router = APIRouter(
    prefix="/permissions",
    tags=["Permissions"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Permission, status_code=status.HTTP_201_CREATED)
async def create_new_permission(
    permission: schemas.PermissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Solo usuarios autenticados
):
    """
    Crea un nuevo permiso.
    NOTA: En un entorno de producción, esta operación debería estar restringida
    solo a usuarios con permisos de administrador.
    """
    db_permission = await crud.get_permission_by_name(db, name=permission.name)
    if db_permission:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Permission with this name already exists"
        )
    
    # Verificar si el module_id proporcionado existe si se especifica
    if permission.module_id:
        db_module = await crud.get_module(db, module_id=permission.module_id)
        if not db_module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module not found."
            )

    return await crud.create_permission(db=db, permission=permission)

@router.get("/{permission_id}", response_model=schemas.Permission)
async def read_permission(
    permission_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Solo usuarios autenticados
):
    """
    Obtiene un permiso por su ID.
    """
    db_permission = await crud.get_permission(db, permission_id=permission_id)
    if db_permission is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    return db_permission

@router.get("/", response_model=List[schemas.Permission])
async def read_permissions(
    skip: int = 0, 
    limit: int = 100, 
    module_id: Optional[uuid.UUID] = None, # Filtro opcional por module_id
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Solo usuarios autenticados
):
    """
    Obtiene una lista de permisos, opcionalmente filtrada por ID de módulo.
    """
    if module_id:
        permissions = await crud.get_permissions_by_module(db, module_id=module_id, skip=skip, limit=limit)
    else:
        permissions = await crud.get_permissions(db, skip=skip, limit=limit)
    return permissions

@router.put("/{permission_id}", response_model=schemas.Permission)
async def update_existing_permission(
    permission_id: uuid.UUID,
    permission_update: schemas.PermissionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Solo usuarios autenticados
):
    """
    Actualiza un permiso existente por su ID.
    NOTA: En un entorno de producción, esta operación debería estar restringida
    solo a usuarios con permisos de administrador.
    """
    db_permission = await crud.get_permission(db, permission_id=permission_id)
    if db_permission is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    # Opcional: Verificar si el nuevo nombre ya existe si se está actualizando el nombre
    if permission_update.name and permission_update.name != db_permission.name:
        existing_permission_with_name = await crud.get_permission_by_name(db, name=permission_update.name)
        if existing_permission_with_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Permission with this name already exists."
            )

    # Si se intenta cambiar el module_id, verificar el nuevo módulo
    if permission_update.module_id is not None and permission_update.module_id != db_permission.module_id:
        new_module = await crud.get_module(db, module_id=permission_update.module_id)
        if not new_module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="New module for permission update not found."
            )

    updated_permission = await crud.update_permission(db, permission_id=permission_id, permission_update=permission_update)
    return updated_permission

@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_permission(
    permission_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Solo usuarios autenticados
):
    """
    Elimina un permiso por su ID.
    NOTA: En un entorno de producción, esta operación debería estar restringida
    solo a usuarios con permisos de administrador.
    """
    success = await crud.delete_permission(db, permission_id=permission_id)
    if not success:
        raise HTTPException(status_code=404, detail="Permission not found")
    return {"message": "Permission deleted successfully"}

