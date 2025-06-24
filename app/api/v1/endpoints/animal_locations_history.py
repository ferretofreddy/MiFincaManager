# routers/animal_locations_history.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Optional

# --- Importaciones de módulos centrales ---
from app import crud, schemas, models # Acceso de alto nivel a tus módulos principales

# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI (get_db, get_current_user, etc.)

router = APIRouter(
    prefix="/animal-location-history",
    tags=["Animal Location History"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.AnimalLocationHistory, status_code=status.HTTP_201_CREATED)
async def create_new_animal_location_history(
    location_history: schemas.AnimalLocationHistory, # CAMBIO: AnimalLocationHistoryBase a AnimalLocationHistory
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Solo usuarios autenticados
):
    """
    Crea un nuevo registro de historial de ubicación para un animal.
    Verifica que el animal y la finca existan y que el usuario actual tenga acceso a la finca.
    """
    db_animal = await crud.get_animal(db, animal_id=location_history.animal_id)
    if not db_animal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Animal not found."
        )
    
    db_farm = await crud.get_farm(db, farm_id=location_history.farm_id)
    if not db_farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found."
        )
    
    # Verificar que el usuario tenga acceso a la finca (sea propietario o tenga acceso compartido)
    user_farms_owned = await crud.get_farms_by_owner_id(db, owner_user_id=current_user.id)
    user_farm_accesses = await crud.get_user_farm_accesses_by_user(db, user_id=current_user.id)
    
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

    # Opcional: Verificar que el animal pertenezca al usuario actual o a la finca.
    # Esta lógica puede ser más compleja dependiendo de las reglas de negocio.
    # Por ahora, solo se verifica que el animal exista, el acceso se basa en la finca.
    # Es posible que el animal ya no esté en la finca del usuario, pero el usuario sí tenga acceso a registrar su historial.
    # Si quieres un chequeo más estricto sobre la propiedad del animal, se añadiría aquí.
    
    return await crud.create_animal_location_history(db=db, location_history=location_history)

@router.get("/{location_history_id}", response_model=schemas.AnimalLocationHistory)
async def read_animal_location_history(
    location_history_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Solo usuarios autenticados
):
    """
    Obtiene un registro de historial de ubicación por su ID.
    Verifica que el usuario actual tenga acceso a la finca asociada.
    """
    db_location = await crud.get_animal_location_history(db, location_history_id=location_history_id)
    if db_location is None:
        raise HTTPException(status_code=404, detail="Animal location history not found")
    
    # Verificar acceso a la finca asociada al historial
    # Un usuario puede ver el historial si tiene acceso a la finca del registro
    # o si es propietario del animal en ese registro.
    user_farms_owned = await crud.get_farms_by_owner_id(db, owner_user_id=current_user.id)
    user_farm_accesses = await crud.get_user_farm_accesses_by_user(db, user_id=current_user.id)

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
    current_user: models.User = Depends(get_current_user) # Solo usuarios autenticados
):
    """
    Obtiene el historial de ubicaciones para un animal específico.
    Verifica que el usuario actual sea propietario del animal o tenga acceso a las fincas en el historial.
    """
    db_animal = await crud.get_animal(db, animal_id=animal_id)
    if not db_animal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Animal not found."
        )

    # Verificar si el usuario es dueño del animal
    if str(db_animal.owner_user_id) != str(current_user.id):
        # Si no es dueño directo, debe tener acceso a CADA finca en el historial de ubicaciones.
        # Esto puede ser ineficiente si hay muchos registros. Una mejor forma sería filtrar en la DB
        # o restringir el acceso a solo animales del usuario.
        user_farms_owned_ids = {str(f.id) for f in await crud.get_farms_by_owner_id(db, owner_user_id=current_user.id)}
        user_farm_access_ids = {str(access.farm_id) for access in await crud.get_user_farm_accesses_by_user(db, user_id=current_user.id)}
        
        all_allowed_farm_ids = user_farms_owned_ids.union(user_farm_access_ids)

        all_location_history_for_animal = await crud.get_animal_location_history_by_animal(db, animal_id=animal_id, skip=0, limit=None)
        
        # Filtrar solo los registros de historial para los cuales el usuario tiene acceso a la finca o es dueño del animal
        filtered_locations = [
            loc for loc in all_location_history_for_animal
            if (loc.farm and str(loc.farm.id) in all_allowed_farm_ids) or str(db_animal.owner_user_id) == str(current_user.id)
        ]
        
        # Aplicar paginación después del filtrado
        return filtered_locations[skip : skip + limit]

    location_history_records = await crud.get_animal_location_history_by_animal(db, animal_id=animal_id, skip=skip, limit=limit)
    return location_history_records


@router.put("/{location_history_id}", response_model=schemas.AnimalLocationHistory)
async def update_existing_animal_location_history(
    location_history_id: uuid.UUID,
    location_history_update: schemas.AnimalLocationHistory, # CAMBIO: AnimalLocationHistoryBase a AnimalLocationHistory
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Solo usuarios autenticados
):
    """
    Actualiza un registro de historial de ubicación existente.
    Verifica que el usuario actual tenga acceso a la finca asociada al registro.
    """
    db_location = await crud.get_animal_location_history(db, location_history_id=location_history_id)
    if not db_location:
        raise HTTPException(status_code=404, detail="Animal location history not found")
    
    # Verificar acceso de actualización (similar a lectura, pero con énfasis en el control del propietario/acceso)
    user_farms_owned_ids = {str(f.id) for f in await crud.get_farms_by_owner_id(db, owner_user_id=current_user.id)}
    user_farm_access_ids = {str(access.farm_id) for access in await crud.get_user_farm_accesses_by_user(db, user_id=current_user.id)}
    
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
        new_animal = await crud.get_animal(db, animal_id=location_history_update.animal_id)
        if not new_animal:
            raise HTTPException(status_code=404, detail="New animal for location history update not found.")
        # Se debería verificar que el usuario tenga permisos sobre el nuevo animal también.
        if str(new_animal.owner_user_id) != str(current_user.id) and \
           not (new_animal.current_lot and new_animal.current_lot.farm and str(new_animal.current_lot.farm.id) in all_allowed_farm_ids):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to assign to this new animal.")


    if location_history_update.farm_id is not None and location_history_update.farm_id != db_location.farm_id:
        new_farm = await crud.get_farm(db, farm_id=location_history_update.farm_id)
        if not new_farm:
            raise HTTPException(status_code=404, detail="New farm for location history update not found.")
        # Se debería verificar que el usuario tenga permisos sobre la nueva finca.
        if str(new_farm.id) not in all_allowed_farm_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to move to this new farm.")

    updated_location = await crud.update_animal_location_history(db, location_history_id=location_history_id, location_history_update=location_history_update)
    return updated_location

@router.delete("/{location_history_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_animal_location_history(
    location_history_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Solo usuarios autenticados
):
    """
    Elimina un registro de historial de ubicación por su ID.
    Verifica que el usuario actual tenga acceso a la finca asociada al registro.
    """
    db_location = await crud.get_animal_location_history(db, location_history_id=location_history_id)
    if not db_location:
        raise HTTPException(status_code=404, detail="Animal location history not found")

    # Verificar acceso de eliminación (similar a lectura/actualización)
    user_farms_owned_ids = {str(f.id) for f in await crud.get_farms_by_owner_id(db, owner_user_id=current_user.id)}
    user_farm_access_ids = {str(access.farm_id) for access in await crud.get_user_farm_accesses_by_user(db, user_id=current_user.id)}
    
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

    success = await crud.delete_animal_location_history(db, location_history_id=location_history_id)
    if not success:
        raise HTTPException(status_code=404, detail="Animal location history not found or could not be deleted")
    return {"message": "Animal location history deleted successfully"}

