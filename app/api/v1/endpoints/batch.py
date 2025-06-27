# app/api/v1/endpoints/batches.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Optional

from app import schemas, models
from app.crud import batch as crud_batch
from app.crud import master_data as crud_master_data
from app.crud import farm as crud_farm
from app.crud import animal as crud_animal
from app.crud import user_farm_access as crud_user_farm_access # Para validación de acceso a fincas

from app.api import deps

get_db = deps.get_db
get_current_active_user = deps.get_current_active_user

router = APIRouter(
    prefix="/batches",
    tags=["Batches"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Batch, status_code=status.HTTP_201_CREATED)
async def create_new_batch(
    batch_in: schemas.BatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Crea un nuevo lote (Batch) de animales.
    Requiere autenticación.
    Valida la existencia del tipo de lote (batch_type_id) en MasterData.
    Valida la existencia de la finca (farm_id) y que el usuario tenga acceso a ella.
    Valida que los animales asociados (animal_ids) existan y sean accesibles por el usuario.
    """
    # 1. Validar MasterData para batch_type_id
    if batch_in.batch_type_id:
        db_batch_type = await crud_master_data.get(db, id=batch_in.batch_type_id)
        if not db_batch_type or db_batch_type.category != "batch_type": # Asume categoría "batch_type"
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch type not found or invalid category."
            )

    # 2. Validar que la finca exista y el usuario tenga acceso a ella
    db_farm = await crud_farm.get(db, id=batch_in.farm_id)
    if not db_farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found."
        )
    
    is_farm_owner = db_farm.owner_user_id == current_user.id
    has_farm_access = False
    if not is_farm_owner:
        user_farm_accesses = await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)
        if any(access.farm_id == db_farm.id for access in user_farm_accesses):
            has_farm_access = True
    
    if not (is_farm_owner or has_farm_access):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create batches in this farm."
        )

    # 3. Validar que los animales existen y son accesibles por el usuario
    if batch_in.animal_ids:
        # Obtener IDs de fincas del usuario (propietario y acceso compartido)
        user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
        user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
        all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

        for animal_id in batch_in.animal_ids:
            db_animal = await crud_animal.get(db, id=animal_id)
            if not db_animal:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Animal with ID {animal_id} not found."
                )
            
            is_animal_owner = db_animal.owner_user_id == current_user.id
            has_animal_farm_access = False
            if not is_animal_owner and db_animal.current_lot and db_animal.current_lot.farm:
                if db_animal.current_lot.farm.id in all_accessible_farm_ids:
                    has_animal_farm_access = True
            
            if not (is_animal_owner or has_animal_farm_access):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Not authorized to associate animal with ID {animal_id} with this batch."
                )

    try:
        db_batch = await crud_batch.create(
            db=db, 
            obj_in=batch_in, 
            created_by_user_id=current_user.id,
            animal_ids=batch_in.animal_ids # Pasa la lista de IDs al CRUD para la tabla pivot
        )
        return db_batch
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating batch: {e}")

@router.get("/{batch_id}", response_model=schemas.Batch)
async def read_batch(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtiene un lote (Batch) por su ID.
    Requiere autenticación y el usuario debe tener acceso a la finca del lote.
    """
    db_batch = await crud_batch.get(db, id=batch_id)
    if not db_batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    is_farm_owner = db_batch.farm.owner_user_id == current_user.id
    has_farm_access = False
    if not is_farm_owner:
        user_farm_accesses = await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)
        if any(access.farm_id == db_batch.farm.id for access in user_farm_accesses):
            has_farm_access = True
    
    if not (is_farm_owner or has_farm_access):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this batch."
        )
    return db_batch

@router.get("/", response_model=List[schemas.Batch])
async def read_batches(
    skip: int = 0,
    limit: int = 100,
    farm_id: Optional[uuid.UUID] = None, # Filtrar por finca
    batch_type_id: Optional[uuid.UUID] = None, # Filtrar por tipo de lote
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtiene una lista de lotes (Batches) a los que el usuario tiene acceso.
    Permite filtrar por farm_id y batch_type_id.
    """
    # Lógica de autorización y filtrado delegada al CRUD para eficiencia
    batches = await crud_batch.get_multi_by_user_and_filters(
        db,
        current_user_id=current_user.id,
        farm_id=farm_id,
        batch_type_id=batch_type_id,
        skip=skip,
        limit=limit
    )
    return batches

@router.put("/{batch_id}", response_model=schemas.Batch)
async def update_existing_batch(
    batch_id: uuid.UUID,
    batch_update: schemas.BatchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Actualiza un lote (Batch) existente por su ID.
    Requiere autenticación y el usuario debe tener acceso a la finca del lote.
    """
    db_batch = await crud_batch.get(db, id=batch_id)
    if not db_batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    is_farm_owner = db_batch.farm.owner_user_id == current_user.id
    has_farm_access = False
    if not is_farm_owner:
        user_farm_accesses = await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)
        if any(access.farm_id == db_batch.farm.id for access in user_farm_accesses):
            has_farm_access = True
    
    if not (is_farm_owner or has_farm_access):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this batch."
        )

    # Validar MasterData para batch_type_id si se actualiza
    if batch_update.batch_type_id is not None and batch_update.batch_type_id != db_batch.batch_type_id:
        db_batch_type = await crud_master_data.get(db, id=batch_update.batch_type_id)
        if not db_batch_type or db_batch_type.category != "batch_type":
            raise HTTPException(status_code=400, detail=f"New batch type with ID '{batch_update.batch_type_id}' not found or invalid category.")

    # Validar que la finca exista si se actualiza y el usuario tenga acceso
    if batch_update.farm_id is not None and batch_update.farm_id != db_batch.farm_id:
        new_farm = await crud_farm.get(db, id=batch_update.farm_id)
        if not new_farm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New farm for batch update not found.")
        
        is_new_farm_owner = new_farm.owner_user_id == current_user.id
        has_new_farm_access = False
        if not is_new_farm_owner:
            user_farm_accesses = await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)
            if any(access.farm_id == new_farm.id for access in user_farm_accesses):
                has_new_farm_access = True
        
        if not (is_new_farm_owner or has_new_farm_access):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to move batch to this new farm."
            )

    # Validar animal_ids si se están actualizando
    if batch_update.animal_ids is not None:
        user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
        user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
        all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

        for animal_id in batch_update.animal_ids:
            db_animal = await crud_animal.get(db, id=animal_id)
            if not db_animal:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Animal with ID {animal_id} not found for update."
                )
            is_animal_owner = db_animal.owner_user_id == current_user.id
            has_animal_farm_access = False
            if not is_animal_owner and db_animal.current_lot and db_animal.current_lot.farm:
                if db_animal.current_lot.farm.id in all_accessible_farm_ids:
                    has_animal_farm_access = True
            
            if not (is_animal_owner or has_animal_farm_access):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Not authorized to associate animal with ID {animal_id} with this batch update."
                )

    try:
        updated_batch = await crud_batch.update(
            db, 
            db_obj=db_batch, 
            obj_in=batch_update, 
            animal_ids=batch_update.animal_ids if batch_update.animal_ids is not None else None
        )
        return updated_batch
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating batch: {e}")

@router.delete("/{batch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_batch(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Elimina un lote (Batch) por su ID.
    Requiere autenticación y el usuario debe tener acceso a la finca del lote.
    """
    db_batch = await crud_batch.get(db, id=batch_id)
    if not db_batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    is_farm_owner = db_batch.farm.owner_user_id == current_user.id
    has_farm_access = False
    if not is_farm_owner:
        user_farm_accesses = await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)
        if any(access.farm_id == db_batch.farm.id for access in user_farm_accesses):
            has_farm_access = True
    
    if not (is_farm_owner or has_farm_access):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this batch."
        )
    
    deleted_batch = await crud_batch.remove(db, id=batch_id)
    if not deleted_batch:
        raise HTTPException(status_code=404, detail="Batch not found or could not be deleted")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

