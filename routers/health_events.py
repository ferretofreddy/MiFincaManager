# routers/health_events.py
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
    prefix="/health-events",
    tags=["Health Events"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.HealthEvent, status_code=status.HTTP_201_CREATED)
async def create_new_health_event(
    health_event: schemas.HealthEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Crea un nuevo evento de salud y lo asocia a los animales especificados.
    Requiere autenticación.
    Verifica que los animales existan y el usuario tenga acceso a ellos.
    Si se proporciona product_id, verifica que el MasterData exista y sea de categoría 'product'.
    """
    # 1. Verificar MasterData para product_id
    if health_event.product_id:
        db_product = await crud.get_master_data(db, master_data_id=health_event.product_id)
        if not db_product or db_product.category != "product":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found or invalid category. Must be a 'product' type MasterData."
            )

    # 2. Verificar animales y permisos
    if not health_event.animal_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one animal_id must be provided for the health event."
        )

    # Lista para almacenar los objetos Animal verificados
    db_animals = []
    for animal_id in health_event.animal_ids:
        db_animal = await crud.get_animal(db, animal_id=animal_id)
        if not db_animal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Animal with ID {animal_id} not found."
            )
        
        # Verificar permisos de acceso al animal
        is_animal_owner = db_animal.owner_user_id == current_user.id
        has_animal_farm_access = False
        if not is_animal_owner and db_animal.current_lot:
            # Re-cargar la finca si no está cargada para la verificación de acceso
            await db.refresh(db_animal.current_lot, attribute_names=["farm"])
            if db_animal.current_lot.farm.owner_user_id == current_user.id:
                has_animal_farm_access = True
            else:
                user_farm_accesses = await crud.get_user_farm_accesses_by_user(db, user_id=current_user.id)
                if any(access.farm_id == db_animal.current_lot.farm.id for access in user_farm_accesses):
                    has_animal_farm_access = True
        
        if not (is_animal_owner or has_animal_farm_access):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to associate animal with ID {animal_id} with a health event."
            )
        db_animals.append(db_animal)

    # 3. Crear el evento de salud
    created_health_event = await crud.create_health_event(
        db=db, 
        health_event=health_event, 
        administered_by_user_id=current_user.id,
        animal_ids=health_event.animal_ids # Pasa la lista de IDs al CRUD
    )
    return created_health_event

@router.get("/", response_model=List[schemas.HealthEvent])
async def read_health_events(
    skip: int = 0,
    limit: int = 100,
    animal_id: Optional[uuid.UUID] = None, # Opcional: filtrar por animal
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene una lista de eventos de salud a los que el usuario tiene acceso.
    Permite filtrar por animal_id.
    """
    # Lógica de autorización: el usuario debe ser el creador del evento o tener acceso a alguno de los animales afectados.
    # Obtener IDs de fincas del usuario (propietario)
    user_owned_farms = await crud.get_farms_by_owner_id(db, owner_user_id=current_user.id)
    user_owned_farm_ids = {f.id for f in user_owned_farms}

    # Obtener IDs de fincas a las que el usuario tiene acceso compartido
    user_farm_accesses = await crud.get_user_farm_accesses_by_user(db, user_id=current_user.id)
    user_shared_farm_ids = {a.farm_id for a in user_farm_accesses}

    # Combinar todas las fincas a las que el usuario tiene acceso
    all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

    health_events = await crud.get_health_events_with_filters(
        db,
        user_id=current_user.id,
        accessible_farm_ids=list(all_accessible_farm_ids),
        animal_id=animal_id,
        skip=skip,
        limit=limit
    )
    return health_events

@router.get("/{event_id}", response_model=schemas.HealthEvent)
async def read_health_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene un evento de salud por su ID.
    El usuario debe ser quien lo administró o tener acceso a alguno de los animales afectados.
    """
    db_health_event = await crud.get_health_event(db, health_event_id=event_id)
    if not db_health_event:
        raise HTTPException(status_code=404, detail="Health event not found")
    
    # Verificar autorización para el evento
    is_admin_user = db_health_event.administered_by_user_id == current_user.id
    
    has_access_to_any_animal = False
    for pivot in db_health_event.animals_affected:
        db_animal = pivot.animal # Animal debería estar cargado por selectinload en get_health_event
        if db_animal:
            is_animal_owner = db_animal.owner_user_id == current_user.id
            has_animal_farm_access = False
            if not is_animal_owner and db_animal.current_lot:
                # Si 'farm' no está cargado ya por el selectinload en get_animal, cargarlo
                await db.refresh(db_animal.current_lot, attribute_names=["farm"])
                if db_animal.current_lot.farm.owner_user_id == current_user.id:
                    has_animal_farm_access = True
                else:
                    user_farm_accesses = await crud.get_user_farm_accesses_by_user(db, user_id=current_user.id)
                    if any(access.farm_id == db_animal.current_lot.farm.id for access in user_farm_accesses):
                        has_animal_farm_access = True
            
            if is_animal_owner or has_animal_farm_access:
                has_access_to_any_animal = True
                break # Si tiene acceso a un solo animal, es suficiente

    if not (is_admin_user or has_access_to_any_animal):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this health event."
        )
    return db_health_event

@router.put("/{event_id}", response_model=schemas.HealthEvent)
async def update_existing_health_event(
    event_id: uuid.UUID,
    health_event_update: schemas.HealthEventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Actualiza un evento de salud existente.
    Solo el usuario que lo administró puede actualizarlo.
    """
    db_health_event = await crud.get_health_event(db, health_event_id=event_id)
    if not db_health_event:
        raise HTTPException(status_code=404, detail="Health event not found")
    
    # Solo el administrador del evento puede actualizarlo
    if db_health_event.administered_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this health event."
        )

    # Verificar MasterData para product_id si se está actualizando
    if health_event_update.product_id is not None and health_event_update.product_id != db_health_event.product_id:
        db_product = await crud.get_master_data(db, master_data_id=health_event_update.product_id)
        if not db_product or db_product.category != "product":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="New product not found or invalid category. Must be a 'product' type MasterData."
            )

    updated_event = await crud.update_health_event(db, health_event_id=event_id, health_event_update=health_event_update)
    return updated_event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_health_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Elimina un evento de salud por su ID.
    Solo el usuario que lo administró puede eliminarlo.
    """
    db_health_event = await crud.get_health_event(db, health_event_id=event_id)
    if not db_health_event:
        raise HTTPException(status_code=404, detail="Health event not found")
    
    # Solo el administrador del evento puede eliminarlo
    if db_health_event.administered_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this health event."
        )
    
    success = await crud.delete_health_event(db, health_event_id=event_id)
    if not success:
        raise HTTPException(status_code=404, detail="Health event not found or could not be deleted")
    return {"message": "Health event deleted successfully"}

