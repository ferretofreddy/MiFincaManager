# app/api/v1/endpoints/animal_location_history.py
from fastapi import APIRouter, Depends, HTTPException, status, Response # Importa Response
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Optional

# --- Importaciones de módulos centrales ---
from app import schemas, models
from app.crud import animal_location_history as crud_animal_location_history
from app.crud import animal as crud_animal
from app.crud import farm as crud_farm
from app.crud import user_farm_access as crud_user_farm_access


# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI

get_db = deps.get_db
get_current_active_user = deps.get_current_active_user


router = APIRouter(
    prefix="/animal-location-history",
    tags=["Animal Location History"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.AnimalLocationHistory, status_code=status.HTTP_201_CREATED)
async def create_new_animal_location_history(
    location_history_in: schemas.AnimalLocationHistoryCreate, # Renombrado y tipo ajustado
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Crea un nuevo registro de historial de ubicación para un animal.
    Verifica que el animal y la finca existan y que el usuario actual tenga acceso a la finca.
    """
    db_animal = await crud_animal.get(db, id=location_history_in.animal_id) # Usar crud_animal
    if not db_animal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Animal not found."
        )
    
    db_farm = await crud_farm.get(db, id=location_history_in.farm_id) # Usar crud_farm
    if not db_farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found."
        )
    
    # Verificar que el usuario tenga acceso a la finca (sea propietario o tenga acceso compartido)
    user_farms_owned = await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id) # Usar crud_farm
    user_farm_accesses = await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id) # Usar crud_user_farm_access
    
    has_farm_access = False
    if str(db_farm.id) in {str(f.id) for f in user_farms_owned}:
        has_farm_access = True
    elif any(str(access.farm_id) == str(db_farm.id) for access in user_farm_accesses):
        has_farm_access = True

    if not has_farm_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create location history for this farm."
        )

    # Opcional: Lógica para cerrar la ubicación anterior del animal si existe
    # Esto se manejaría en el CRUD de AnimalLocationHistory.create o se llamaría desde aquí
    
    return await crud_animal_location_history.create(db=db, obj_in=location_history_in, created_by_user_id=current_user.id) # Usar crud_animal_location_history

@router.get("/{location_history_id}", response_model=schemas.AnimalLocationHistory)
async def read_animal_location_history(
    location_history_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtiene un registro de historial de ubicación por su ID.
    Verifica que el usuario actual tenga acceso a la finca asociada.
    """
    db_location = await crud_animal_location_history.get(db, id=location_history_id) # Usar crud_animal_location_history
    if db_location is None:
        raise HTTPException(status_code=404, detail="Animal location history not found")
    
    # Verificar acceso a la finca asociada al historial
    # Un usuario puede ver el historial si tiene acceso a la finca del registro
    # o si es propietario del animal en ese registro.
    user_farms_owned = await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id) # Usar crud_farm
    user_farm_accesses = await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id) # Usar crud_user_farm_access

    has_access = False
    if db_location.farm and str(db_location.farm.owner_user_id) == str(current_user.id):
        has_access = True # Es el dueño de la finca del historial
    elif db_location.farm and any(str(access.farm_id) == str(db_location.farm.id) for access in user_farm_accesses):
        has_access = True # Tiene acceso compartido a la finca del historial
    elif db_location.animal and str(db_location.animal.owner_user_id) == str(current_user.id):
        has_access = True # Es el dueño del animal del historial

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this animal location history."
        )
    
    return db_location

@router.get("/animal/{animal_id}", response_model=List[schemas.AnimalLocationHistory])
async def read_animal_locations_by_animal(
    animal_id: uuid.UUID,
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtiene el historial de ubicaciones para un animal específico.
    Verifica que el usuario actual sea propietario del animal o tenga acceso a las fincas en el historial.
    """
    db_animal = await crud_animal.get(db, id=animal_id) # Usar crud_animal
    if not db_animal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Animal not found."
        )

    # Lógica de autorización compleja que debería estar en el CRUD para eficiencia.
    # Se asume un método crud_animal_location_history.get_multi_by_animal_id_and_access
    location_history_records = await crud_animal_location_history.get_multi_by_animal_id_and_access(
        db, 
        animal_id=animal_id,
        current_user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return location_history_records


@router.put("/{location_history_id}", response_model=schemas.AnimalLocationHistory)
async def update_existing_animal_location_history(
    location_history_id: uuid.UUID,
    location_history_update: schemas.AnimalLocationHistoryUpdate, # Ajustado a Update schema
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Actualiza un registro de historial de ubicación existente.
    Verifica que el usuario actual tenga acceso a la finca asociada al registro.
    """
    db_location = await crud_animal_location_history.get(db, id=location_history_id) # Usar crud_animal_location_history
    if not db_location:
        raise HTTPException(status_code=404, detail="Animal location history not found")
    
    # Verificar acceso de actualización (similar a lectura, pero con énfasis en el control del propietario/acceso)
    user_farms_owned_ids = {str(f.id) for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)} # Usar crud_farm
    user_farm_access_ids = {str(access.farm_id) for access in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)} # Usar crud_user_farm_access
    
    all_allowed_farm_ids = user_farms_owned_ids.union(user_farm_access_ids)

    has_access = False
    if db_location.farm and str(db_location.farm.id) in all_allowed_farm_ids:
        has_access = True # Tiene acceso a la finca del historial
    elif db_location.animal and str(db_location.animal.owner_user_id) == str(current_user.id):
        has_access = True # Es el dueño del animal del historial
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this animal location history."
        )

    # Si se intenta cambiar animal_id o farm_id, realizar verificaciones adicionales
    if location_history_update.animal_id is not None and location_history_update.animal_id != db_location.animal_id:
        new_animal = await crud_animal.get(db, id=location_history_update.animal_id) # Usar crud_animal
        if not new_animal:
            raise HTTPException(status_code=404, detail="New animal for location history update not found.")
        # Se debería verificar que el usuario tenga permisos sobre el nuevo animal también.
        # Es propietario del nuevo animal o tiene acceso a su finca.
        is_new_animal_owner = new_animal.owner_user_id == current_user.id
        has_new_animal_farm_access = False
        if not is_new_animal_owner and new_animal.current_lot and new_animal.current_lot.farm:
            if new_animal.current_lot.farm.id in all_allowed_farm_ids:
                has_new_animal_farm_access = True
        
        if not (is_new_animal_owner or has_new_animal_farm_access):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to assign to this new animal.")


    if location_history_update.farm_id is not None and location_history_update.farm_id != db_location.farm_id:
        new_farm = await crud_farm.get(db, id=location_history_update.farm_id) # Usar crud_farm
        if not new_farm:
            raise HTTPException(status_code=404, detail="New farm for location history update not found.")
        # Se debería verificar que el usuario tenga permisos sobre la nueva finca.
        if str(new_farm.id) not in all_allowed_farm_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to move to this new farm.")

    updated_location = await crud_animal_location_history.update(db, db_obj=db_location, obj_in=location_history_update) # Usar crud_animal_location_history
    return updated_location

@router.delete("/{location_history_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_animal_location_history(
    location_history_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Elimina un registro de historial de ubicación por su ID.
    Verifica que el usuario actual tenga acceso a la finca asociada al registro.
    """
    db_location = await crud_animal_location_history.get(db, id=location_history_id) # Usar crud_animal_location_history
    if not db_location:
        raise HTTPException(status_code=404, detail="Animal location history not found")

    # Verificar acceso de eliminación (similar a lectura/actualización)
    user_farms_owned_ids = {str(f.id) for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)} # Usar crud_farm
    user_farm_access_ids = {str(access.farm_id) for access in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)} # Usar crud_user_farm_access
    
    all_allowed_farm_ids = user_farms_owned_ids.union(user_farm_access_ids)

    has_access = False
    if db_location.farm and str(db_location.farm.id) in all_allowed_farm_ids:
        has_access = True # Tiene acceso a la finca del historial
    elif db_location.animal and str(db_location.animal.owner_user_id) == str(current_user.id):
        has_access = True # Es el dueño del animal del historial
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this animal location history."
        )

    deleted_location = await crud_animal_location_history.remove(db, id=location_history_id) # Usar crud_animal_location_history
    if not deleted_location:
        raise HTTPException(status_code=404, detail="Animal location history not found or could not be deleted")
    return Response(status_code=status.HTTP_204_NO_CONTENT) # Retorno correcto para 204

