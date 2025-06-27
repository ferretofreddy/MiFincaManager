# app/api/v1/endpoints/grupos.py
from fastapi import APIRouter, Depends, HTTPException, status, Response # Importa Response
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Optional

# --- Importaciones de módulos centrales ---
from app import schemas, models
from app.crud import grupo as crud_grupo # Importa la instancia CRUD para grupo
from app.crud import master_data as crud_master_data # Importa la instancia CRUD para master_data


# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI

# Asumiendo que 'get_db' y 'get_current_active_user' etc. estarán en 'app/api/deps.py'
get_db = deps.get_db
get_current_active_user = deps.get_current_active_user


router = APIRouter(
    prefix="/grupos",
    tags=["Grupos"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Grupo, status_code=status.HTTP_201_CREATED)
async def create_new_grupo(
    grupo_in: schemas.GrupoCreate, # Renombrado
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Crea un nuevo grupo.
    Requiere autenticación.
    Si se proporciona purpose_id, verifica que el MasterData exista y sea de categoría 'purpose'.
    """
    if grupo_in.purpose_id:
        db_purpose = await crud_master_data.get(db, id=grupo_in.purpose_id) # Usar crud_master_data
        if not db_purpose or db_purpose.category != "purpose":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purpose not found or invalid category."
            )
    
    # Verificar si ya existe un grupo con el mismo nombre creado por el mismo usuario
    existing_grupo = await crud_grupo.get_by_name_and_user_id(db, name=grupo_in.name, created_by_user_id=current_user.id) # Asume este método en crud_grupo
    if existing_grupo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Group with name '{grupo_in.name}' already exists for this user."
        )
    
    db_grupo = await crud_grupo.create(db=db, obj_in=grupo_in, created_by_user_id=current_user.id) # Usar crud_grupo
    return db_grupo

@router.get("/{grupo_id}", response_model=schemas.Grupo)
async def read_grupo(
    grupo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtiene un grupo por su ID.
    El usuario debe ser quien lo creó.
    """
    db_grupo = await crud_grupo.get(db, id=grupo_id) # Usar crud_grupo
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
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtiene una lista de grupos creados por el usuario autenticado.
    """
    # Usar la función que filtra por el usuario creador
    grupos = await crud_grupo.get_multi_by_created_by_user_id(db, created_by_user_id=current_user.id, skip=skip, limit=limit) # Usar crud_grupo
    return grupos

@router.put("/{grupo_id}", response_model=schemas.Grupo)
async def update_existing_grupo(
    grupo_id: uuid.UUID,
    grupo_update: schemas.GrupoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Actualiza un grupo existente por su ID.
    Solo el usuario que lo creó puede actualizarlo.
    """
    db_grupo = await crud_grupo.get(db, id=grupo_id) # Usar crud_grupo
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
        db_new_purpose = await crud_master_data.get(db, id=grupo_update.purpose_id) # Usar crud_master_data
        if not db_new_purpose or db_new_purpose.category != "purpose":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New purpose not found or invalid.")

    # Si se actualiza el nombre, verificar unicidad para el mismo usuario
    if grupo_update.name is not None and grupo_update.name != db_grupo.name:
        existing_grupo_with_name = await crud_grupo.get_by_name_and_user_id(db, name=grupo_update.name, created_by_user_id=current_user.id)
        if existing_grupo_with_name and existing_grupo_with_name.id != grupo_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Group with name '{grupo_update.name}' already exists for this user."
            )

    updated_grupo = await crud_grupo.update(db, db_obj=db_grupo, obj_in=grupo_update) # Usar crud_grupo
    return updated_grupo

@router.delete("/{grupo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_grupo(
    grupo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Elimina un grupo por su ID.
    Solo el usuario que lo creó puede eliminarlo.
    """
    db_grupo = await crud_grupo.get(db, id=grupo_id) # Usar crud_grupo
    if not db_grupo:
        raise HTTPException(status_code=404, detail="Grupo not found")
    
    # Solo el creador del grupo puede eliminarlo
    if db_grupo.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this group."
        )
    
    deleted_grupo = await crud_grupo.remove(db, id=grupo_id) # Usar crud_grupo
    if not deleted_grupo:
        raise HTTPException(status_code=404, detail="Grupo not found or could not be deleted")
    return Response(status_code=status.HTTP_204_NO_CONTENT) # Retorno correcto para 204

