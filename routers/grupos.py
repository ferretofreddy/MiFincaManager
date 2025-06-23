# routers/grupos.py
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
    prefix="/grupos",
    tags=["Grupos"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Grupo, status_code=status.HTTP_201_CREATED)
async def create_new_grupo(
    grupo: schemas.GrupoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Crea un nuevo grupo.
    Requiere autenticación.
    Si se proporciona purpose_id, verifica que el MasterData exista y sea de categoría 'purpose'.
    """
    if grupo.purpose_id:
        db_purpose = await crud.get_master_data(db, master_data_id=grupo.purpose_id)
        if not db_purpose or db_purpose.category != "purpose":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purpose not found or invalid category."
            )
    
    # Verificar si ya existe un grupo con el mismo nombre creado por el mismo usuario
    # Aunque no hay una función CRUD específica para esto, se podría añadir si se necesita unicidad estricta.
    # Por ahora, solo se creará.
    
    db_grupo = await crud.create_grupo(db=db, grupo=grupo, created_by_user_id=current_user.id)
    return db_grupo

@router.get("/{grupo_id}", response_model=schemas.Grupo)
async def read_grupo(
    grupo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene un grupo por su ID.
    El usuario debe ser quien lo creó.
    """
    db_grupo = await crud.get_grupo(db, grupo_id=grupo_id)
    if not db_grupo:
        raise HTTPException(status_code=404, detail="Grupo not found")
    
    # Solo el creador del grupo puede acceder a él
    if db_grupo.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this group."
        )
    return db_grupo

@router.get("/", response_model=List[schemas.Grupo])
async def read_grupos(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene una lista de grupos creados por el usuario autenticado.
    """
    # CORRECCIÓN AQUÍ: Usar la nueva función que filtra por el usuario creador
    grupos = await crud.get_grupos_by_created_by_user_id(db, created_by_user_id=current_user.id, skip=skip, limit=limit)
    return grupos

@router.put("/{grupo_id}", response_model=schemas.Grupo)
async def update_existing_grupo(
    grupo_id: uuid.UUID,
    grupo_update: schemas.GrupoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Actualiza un grupo existente por su ID.
    Solo el usuario que lo creó puede actualizarlo.
    """
    db_grupo = await crud.get_grupo(db, grupo_id=grupo_id)
    if not db_grupo:
        raise HTTPException(status_code=404, detail="Grupo not found")
    
    # Solo el creador del grupo puede actualizarlo
    if db_grupo.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this group."
        )

    # Si se intenta cambiar purpose_id, verificar que el MasterData exista y sea de categoría 'purpose'
    if grupo_update.purpose_id is not None and grupo_update.purpose_id != db_grupo.purpose_id:
        db_new_purpose = await crud.get_master_data(db, master_data_id=grupo_update.purpose_id)
        if not db_new_purpose or db_new_purpose.category != "purpose":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New purpose not found or invalid.")

    updated_grupo = await crud.update_grupo(db, grupo_id=grupo_id, grupo_update=grupo_update)
    return updated_grupo

@router.delete("/{grupo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_grupo(
    grupo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Elimina un grupo por su ID.
    Solo el usuario que lo creó puede eliminarlo.
    """
    db_grupo = await crud.get_grupo(db, grupo_id=grupo_id)
    if not db_grupo:
        raise HTTPException(status_code=404, detail="Grupo not found")
    
    # Solo el creador del grupo puede eliminarlo
    if db_grupo.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this group."
        )
    
    success = await crud.delete_grupo(db, grupo_id=grupo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Grupo not found or could not be deleted")
    return {"message": "Grupo deleted successfully"}

