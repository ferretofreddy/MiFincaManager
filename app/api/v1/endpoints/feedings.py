# app/api/v1/endpoints/feedings.py
from fastapi import APIRouter, Depends, HTTPException, status, Response # Importa Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid

# --- Importaciones de módulos centrales ---
from app import schemas, models
from app.crud import feeding as crud_feeding
from app.crud import master_data as crud_master_data
from app.crud import animal as crud_animal
from app.crud import user_farm_access as crud_user_farm_access
from app.crud import farm as crud_farm


# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI

get_db = deps.get_db
get_current_active_user = deps.get_current_active_user


router = APIRouter(
    prefix="/feedings",
    tags=["Feedings"],
    responses={404: {"description": "Not found"}},
)

# --- Rutas de Alimentación ---

@router.post("/", response_model=schemas.Feeding, status_code=status.HTTP_201_CREATED)
async def create_new_feeding(
    feeding_in: schemas.FeedingCreate, # Renombrado
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Crea un nuevo registro de alimentación y lo asocia a los animales proporcionados.
    Se valida si el tipo de alimento, unidad y suplemento (si aplica) existen en MasterData.
    Se valida que los animales existen y son accesibles por el usuario.
    """
    # 1. Validar MasterData para feed_type_id
    if feeding_in.feed_type_id:
        feed_type_data = await crud_master_data.get(db, id=feeding_in.feed_type_id)
        if not feed_type_data or feed_type_data.category != 'feed_type': # Asegúrate de que la categoría es 'feed_type'
            raise HTTPException(status_code=400, detail=f"Feed type with ID '{feeding_in.feed_type_id}' not found or invalid category in MasterData (must be 'feed_type').")

    # 2. Validar MasterData para unit_id
    if feeding_in.unit_id:
        unit_data = await crud_master_data.get(db, id=feeding_in.unit_id)
        if not unit_data or unit_data.category != 'unit_of_measure': # Asegúrate de que la categoría es 'unit_of_measure'
            raise HTTPException(status_code=400, detail=f"Unit with ID '{feeding_in.unit_id}' not found or invalid category in MasterData (must be 'unit_of_measure').")

    # 3. Validar MasterData para supplement_id (si existe)
    if feeding_in.supplement_id:
        supplement_data = await crud_master_data.get(db, id=feeding_in.supplement_id)
        if not supplement_data or supplement_data.category != 'supplement': # Asegúrate de que la categoría es 'supplement'
            raise HTTPException(status_code=400, detail=f"Supplement with ID '{feeding_in.supplement_id}' not found or invalid category in MasterData (must be 'supplement').")

    # 4. Validar que los animales existen y son accesibles por el usuario
    if not feeding_in.animal_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one animal_id must be provided for the feeding event."
        )

    for animal_id in feeding_in.animal_ids:
        animal = await crud_animal.get(db, id=animal_id)
        if not animal:
            raise HTTPException(status_code=400, detail=f"Animal with ID '{animal_id}' not found.")
        
        # Lógica de autorización para cada animal: el usuario debe ser propietario o tener acceso a la finca
        is_animal_owner = animal.owner_user_id == current_user.id
        has_animal_farm_access = False
        if not is_animal_owner and animal.current_lot:
            user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
            user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
            all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

            if animal.current_lot.farm and animal.current_lot.farm.id in all_accessible_farm_ids:
                has_animal_farm_access = True
        
        if not (is_animal_owner or has_animal_farm_access):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to assign feeding to animal with ID '{animal_id}'.")

    try:
        # Pasa feeding_in y administered_by_user_id, junto con animal_ids para el CRUD
        db_feeding = await crud_feeding.create(
            db=db, 
            obj_in=feeding_in, 
            administered_by_user_id=current_user.id,
            animal_ids=feeding_in.animal_ids # Pasa la lista de IDs al CRUD para la tabla pivot
        )
        return db_feeding
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{feeding_id}", response_model=schemas.Feeding)
async def read_feeding(
    feeding_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtiene los detalles de un registro de alimentación específico.
    Solo accesible si el usuario administró el evento o tiene acceso a los animales afectados.
    """
    db_feeding = await crud_feeding.get(db, id=feeding_id)
    if db_feeding is None:
        raise HTTPException(status_code=404, detail="Feeding record not found")
    
    # Lógica de autorización: el usuario debe haber administrado el evento O tener acceso a *al menos uno* de los animales afectados.
    is_admin_user = db_feeding.recorded_by_user_id == current_user.id
    
    has_access_to_any_animal = False
    if db_feeding.animal_feedings: # Si hay asociaciones de animales
        for pivot in db_feeding.animal_feedings:
            db_animal = pivot.animal # Animal debería estar cargado por selectinload en crud.feeding.get
            if db_animal:
                is_animal_owner = db_animal.owner_user_id == current_user.id
                has_animal_farm_access = False
                if not is_animal_owner and db_animal.current_lot:
                    user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
                    user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
                    all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

                    if db_animal.current_lot.farm and db_animal.current_lot.farm.id in all_accessible_farm_ids:
                        has_animal_farm_access = True
                
                if is_animal_owner or has_animal_farm_access:
                    has_access_to_any_animal = True
                    break # Si tiene acceso a un solo animal, es suficiente
    
    if not (is_admin_user or has_access_to_any_animal):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this feeding record.")
    
    return db_feeding

@router.get("/", response_model=List[schemas.Feeding])
async def read_feedings(
    skip: int = 0,
    limit: int = 100,
    animal_id: Optional[uuid.UUID] = None, # Filtro opcional por animal
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtiene una lista de registros de alimentación.
    Solo muestra eventos administrados por el usuario actual o asociados a animales a los que tiene acceso.
    """
    # Se asume que crud_feeding.get_multi_by_user_and_filters_and_access existe
    feedings = await crud_feeding.get_multi_by_user_and_filters_and_access(
        db, 
        current_user_id=current_user.id,
        animal_id=animal_id,
        skip=skip, 
        limit=limit
    )
    return feedings

@router.put("/{feeding_id}", response_model=schemas.Feeding)
async def update_existing_feeding(
    feeding_id: uuid.UUID,
    feeding_update: schemas.FeedingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Actualiza los detalles de un registro de alimentación específico.
    Solo el usuario que lo administró puede actualizarlo.
    """
    db_feeding = await crud_feeding.get(db, id=feeding_id)
    if db_feeding is None:
        raise HTTPException(status_code=404, detail="Feeding record not found")
    
    if str(db_feeding.recorded_by_user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this feeding record.")

    # Validar MasterData para feed_type_id si se actualiza
    if feeding_update.feed_type_id:
        feed_type_data = await crud_master_data.get(db, id=feeding_update.feed_type_id)
        if not feed_type_data or feed_type_data.category != 'feed_type':
            raise HTTPException(status_code=400, detail=f"Feed type with ID '{feeding_update.feed_type_id}' not found or invalid category.")

    # Validar MasterData para unit_id si se actualiza
    if feeding_update.unit_id:
        unit_data = await crud_master_data.get(db, id=feeding_update.unit_id)
        if not unit_data or unit_data.category != 'unit_of_measure':
            raise HTTPException(status_code=400, detail=f"Unit with ID '{feeding_update.unit_id}' not found or invalid category.")

    # Validar MasterData para supplement_id si se actualiza
    if feeding_update.supplement_id:
        supplement_data = await crud_master_data.get(db, id=feeding_update.supplement_id)
        if not supplement_data or supplement_data.category != 'supplement':
            raise HTTPException(status_code=400, detail=f"Supplement with ID '{feeding_update.supplement_id}' not found or invalid category.")

    # Si se actualizan animal_ids, validar y gestionar en el CRUD
    if feeding_update.animal_ids is not None: # Si la lista de IDs se proporciona (puede ser vacía)
        for animal_id in feeding_update.animal_ids:
            animal = await crud_animal.get(db, id=animal_id)
            if not animal:
                raise HTTPException(status_code=400, detail=f"Animal with ID '{animal_id}' not found for update.")
            # La lógica de autorización para los animales debe ser la misma que en la creación.
            is_animal_owner = animal.owner_user_id == current_user.id
            has_animal_farm_access = False
            if not is_animal_owner and animal.current_lot:
                user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
                user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
                all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

                if animal.current_lot.farm and animal.current_lot.farm.id in all_accessible_farm_ids:
                    has_animal_farm_access = True
            
            if not (is_animal_owner or has_animal_farm_access):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to update feeding for animal with ID '{animal_id}'.")


    try:
        # Pasa feeding_update.animal_ids al CRUD para que gestione la tabla pivot
        updated_feeding = await crud_feeding.update(
            db, 
            db_obj=db_feeding, 
            obj_in=feeding_update, 
            animal_ids=feeding_update.animal_ids if feeding_update.animal_ids is not None else None # Pasar None si no se proporciona para no modificar
        )
        if updated_feeding is None:
            raise HTTPException(status_code=500, detail="Failed to update feeding record unexpectedly.") 
        return updated_feeding
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{feeding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_feeding(
    feeding_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Elimina un registro de alimentación específico.
    Solo el usuario que lo administró puede eliminarlo.
    """
    db_feeding = await crud_feeding.get(db, id=feeding_id)
    if db_feeding is None:
        raise HTTPException(status_code=404, detail="Feeding record not found")
    
    if str(db_feeding.recorded_by_user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this feeding record.")
    
    deleted_feeding = await crud_feeding.remove(db, id=feeding_id)
    if not deleted_feeding:
        raise HTTPException(status_code=500, detail="Failed to delete feeding record unexpectedly.")
    return Response(status_code=status.HTTP_204_NO_CONTENT) # Retorno correcto para 204

