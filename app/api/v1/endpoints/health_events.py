# app/api/v1/endpoints/health_events.py
from fastapi import APIRouter, Depends, HTTPException, status, Response # Importa Response
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Optional

# --- Importaciones de módulos centrales ---
from app import schemas, models
from app.crud import health_event as crud_health_event
from app.crud import master_data as crud_master_data
from app.crud import animal as crud_animal
from app.crud import user_farm_access as crud_user_farm_access
from app.crud import farm as crud_farm


# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI

get_db = deps.get_db
get_current_active_user = deps.get_current_active_user


router = APIRouter(
    prefix="/health-events",
    tags=["Health Events"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.HealthEvent, status_code=status.HTTP_201_CREATED)
async def create_new_health_event(
    health_event_in: schemas.HealthEventCreate, # Renombrado
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Crea un nuevo evento de salud y lo asocia a los animales especificados.
    Requiere autenticación.
    Verifica que los animales existan y el usuario tenga acceso a ellos.
    Si se proporciona product_id, verifica que el MasterData exista y sea de categoría 'product' o 'medicine'.
    """
    # 1. Validar MasterData para product_id (si existe)
    if health_event_in.product_id:
        db_product = await crud_master_data.get(db, id=health_event_in.product_id)
        # Ajusta la categoría según tus MasterData (ej. "product" o "medicine")
        if not db_product or (db_product.category != "product" and db_product.category != "medicine"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found or invalid category. Must be a 'product' or 'medicine' type MasterData."
            )

    # 2. Validar que se proporcionen IDs de animales y verificar permisos
    if not health_event_in.animal_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one animal_id must be provided for the health event."
        )

    # Obtener IDs de fincas del usuario (propietario y acceso compartido)
    user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
    user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
    all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

    for animal_id in health_event_in.animal_ids:
        db_animal = await crud_animal.get(db, id=animal_id)
        if not db_animal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Animal with ID {animal_id} not found."
            )
        
        # Verificar permisos de acceso al animal
        is_animal_owner = db_animal.owner_user_id == current_user.id
        has_animal_farm_access = False
        if not is_animal_owner and db_animal.current_lot and db_animal.current_lot.farm:
            if db_animal.current_lot.farm.id in all_accessible_farm_ids:
                has_animal_farm_access = True
        
        if not (is_animal_owner or has_animal_farm_access):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to associate animal with ID {animal_id} with a health event."
            )

    # 3. Crear el evento de salud
    created_health_event = await crud_health_event.create(
        db=db, 
        obj_in=health_event_in, 
        administered_by_user_id=current_user.id,
        animal_ids=health_event_in.animal_ids # Pasa la lista de IDs al CRUD
    )
    return created_health_event

@router.get("/", response_model=List[schemas.HealthEvent])
async def read_health_events(
    skip: int = 0,
    limit: int = 100,
    animal_id: Optional[uuid.UUID] = None, # Opcional: filtrar por animal
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtiene una lista de eventos de salud a los que el usuario tiene acceso.
    Permite filtrar por animal_id.
    """
    # Lógica de autorización y filtrado delegada al CRUD para eficiencia
    health_events = await crud_health_event.get_multi_by_user_and_filters_and_access(
        db,
        current_user_id=current_user.id,
        animal_id=animal_id,
        skip=skip,
        limit=limit
    )
    return health_events

@router.get("/{event_id}", response_model=schemas.HealthEvent)
async def read_health_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtiene un evento de salud por su ID.
    El usuario debe ser quien lo administró o tener acceso a alguno de los animales afectados.
    """
    db_health_event = await crud_health_event.get(db, id=event_id)
    if not db_health_event:
        raise HTTPException(status_code=404, detail="Health event not found")
    
    # Verificar autorización para el evento
    is_admin_user = db_health_event.administered_by_user_id == current_user.id
    
    has_access_to_any_animal = False
    if db_health_event.animals_affected: # Si hay asociaciones de animales
        for pivot in db_health_event.animals_affected:
            db_animal = pivot.animal # Animal debería estar cargado por selectinload en crud.health_event.get
            if db_animal:
                is_animal_owner = db_animal.owner_user_id == current_user.id
                has_animal_farm_access = False
                if not is_animal_owner and db_animal.current_lot and db_animal.current_lot.farm:
                    user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
                    user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
                    all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

                    if db_animal.current_lot.farm.id in all_accessible_farm_ids:
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
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Actualiza un evento de salud existente.
    Solo el usuario que lo administró puede actualizarlo.
    """
    db_health_event = await crud_health_event.get(db, id=event_id)
    if not db_health_event:
        raise HTTPException(status_code=404, detail="Health event not found")
    
    # Solo el administrador del evento puede actualizarlo
    if db_health_event.administered_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this health event."
        )

    # Validar MasterData para product_id si se está actualizando
    if health_event_update.product_id is not None and health_event_update.product_id != db_health_event.product_id:
        db_product = await crud_master_data.get(db, id=health_event_update.product_id)
        if not db_product or (db_product.category != "product" and db_product.category != "medicine"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="New product not found or invalid category. Must be a 'product' or 'medicine' type MasterData."
            )

    # Validar animal_ids si se están actualizando
    if health_event_update.animal_ids is not None:
        user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
        user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
        all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

        for animal_id in health_event_update.animal_ids:
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
                    detail=f"Not authorized to associate animal with ID {animal_id} with this health event update."
                )

    updated_event = await crud_health_event.update(
        db, 
        db_obj=db_health_event, 
        obj_in=health_event_update,
        animal_ids=health_event_update.animal_ids if health_event_update.animal_ids is not None else None
    )
    return updated_event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_health_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Elimina un evento de salud por su ID.
    Solo el usuario que lo administró puede eliminarlo.
    """
    db_health_event = await crud_health_event.get(db, id=event_id)
    if not db_health_event:
        raise HTTPException(status_code=404, detail="Health event not found")
    
    # Solo el administrador del evento puede eliminarlo
    if db_health_event.administered_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this health event."
        )
    
    deleted_event = await crud_health_event.remove(db, id=event_id)
    if not deleted_event:
        raise HTTPException(status_code=404, detail="Health event not found or could not be deleted")
    return Response(status_code=status.HTTP_204_NO_CONTENT) # Retorno correcto para 204

