# app/api/v1/endpoints/reproductive_events.py
from fastapi import APIRouter, Depends, HTTPException, status, Response # Importa Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid

# --- Importaciones de módulos centrales ---
from app import schemas, models
from app.crud import reproductive_event as crud_reproductive_event
from app.crud import offspring_born as crud_offspring_born
from app.crud import animal as crud_animal
from app.crud import user_farm_access as crud_user_farm_access
from app.crud import farm as crud_farm


# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI

get_db = deps.get_db
get_current_active_user = deps.get_current_active_user


router = APIRouter(
    prefix="/reproductive-events",
    tags=["Reproductive Events"],
    responses={404: {"description": "Not found"}},
)

# --- Rutas de Eventos Reproductivos ---

@router.post("/", response_model=schemas.ReproductiveEvent, status_code=status.HTTP_201_CREATED)
async def create_new_reproductive_event(
    event_in: schemas.ReproductiveEventCreate, # Renombrado
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Crea un nuevo evento reproductivo.
    Se valida que el animal (hembra) y el semental (si aplica) existen y son accesibles.
    """
    # 1. Validar que el animal (hembra) existe y pertenece al usuario o su finca
    animal_db = await crud_animal.get(db, id=event_in.animal_id)
    if not animal_db:
        raise HTTPException(status_code=400, detail=f"Animal with ID '{event_in.animal_id}' not found.")
    
    # Lógica de autorización para la hembra: propietario o acceso a la finca
    is_animal_owner = animal_db.owner_user_id == current_user.id
    has_animal_farm_access = False
    if not is_animal_owner and animal_db.current_lot:
        user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
        user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
        all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

        if animal_db.current_lot.farm and animal_db.current_lot.farm.id in all_accessible_farm_ids:
            has_animal_farm_access = True
    
    if not (is_animal_owner or has_animal_farm_access):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to create reproductive event for animal with ID '{event_in.animal_id}'.")

    # 2. Validar que si hay semental, exista y sea accesible
    if event_in.sire_animal_id:
        sire_animal_db = await crud_animal.get(db, id=event_in.sire_animal_id)
        if not sire_animal_db:
            raise HTTPException(status_code=400, detail=f"Sire animal with ID '{event_in.sire_animal_id}' not found.")
        
        # Lógica de autorización para el semental: propietario o acceso a la finca
        is_sire_owner = sire_animal_db.owner_user_id == current_user.id
        has_sire_farm_access = False
        if not is_sire_owner and sire_animal_db.current_lot:
            user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
            user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
            all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

            if sire_animal_db.current_lot.farm and sire_animal_db.current_lot.farm.id in all_accessible_farm_ids:
                has_sire_farm_access = True
        
        if not (is_sire_owner or has_sire_farm_access):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to use sire animal with ID '{event_in.sire_animal_id}'.")

    try:
        db_event = await crud_reproductive_event.create(db=db, obj_in=event_in, administered_by_user_id=current_user.id)
        return db_event
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{event_id}", response_model=schemas.ReproductiveEvent)
async def read_reproductive_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtiene los detalles de un evento reproductivo específico.
    Solo accesible si el usuario es propietario de la hembra o el semental involucrado,
    o tiene acceso a la finca de alguno de ellos.
    """
    db_event = await crud_reproductive_event.get(db, id=event_id)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Reproductive event not found")
    
    # Lógica de autorización: el usuario debe tener acceso a la hembra o al semental
    is_authorized = False

    # Check access to the female animal
    if db_event.animal:
        is_animal_owner = db_event.animal.owner_user_id == current_user.id
        has_animal_farm_access = False
        if not is_animal_owner and db_event.animal.current_lot and db_event.animal.current_lot.farm:
            user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
            user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
            all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

            if db_event.animal.current_lot.farm.id in all_accessible_farm_ids:
                has_animal_farm_access = True
        
        if is_animal_owner or has_animal_farm_access:
            is_authorized = True

    # Check access to the sire animal if exists and not already authorized
    if not is_authorized and db_event.sire_animal:
        is_sire_owner = db_event.sire_animal.owner_user_id == current_user.id
        has_sire_farm_access = False
        if not is_sire_owner and db_event.sire_animal.current_lot and db_event.sire_animal.current_lot.farm:
            user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
            user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
            all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

            if db_event.sire_animal.current_lot.farm.id in all_accessible_farm_ids:
                has_sire_farm_access = True
        
        if is_sire_owner or has_sire_farm_access:
            is_authorized = True

    if not is_authorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this reproductive event.")
    
    return db_event

@router.get("/", response_model=List[schemas.ReproductiveEvent])
async def read_reproductive_events(
    animal_id: Optional[uuid.UUID] = None, # Filtrar por animal (hembra)
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtiene una lista de eventos reproductivos, opcionalmente filtrados por animal (hembra).
    Solo muestra eventos relacionados con animales que el usuario posee o a cuyas fincas tiene acceso.
    """
    # Lógica de autorización y filtrado delegada al CRUD para eficiencia
    # Se asume un método crud_reproductive_event.get_multi_by_user_and_filters_and_access
    events = await crud_reproductive_event.get_multi_by_user_and_filters_and_access(
        db, 
        current_user_id=current_user.id,
        animal_id=animal_id,
        skip=skip, 
        limit=limit
    )
    return events


@router.put("/{event_id}", response_model=schemas.ReproductiveEvent)
async def update_existing_reproductive_event(
    event_id: uuid.UUID,
    event_update: schemas.ReproductiveEventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Actualiza los detalles de un evento reproductivo específico.
    Solo accesible si el usuario es propietario de la hembra o el semental involucrado,
    o tiene acceso a la finca de alguno de ellos.
    """
    db_event = await crud_reproductive_event.get(db, id=event_id)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Reproductive event not found")
    
    is_authorized = False

    # Check access to the female animal (current or new if updated)
    animal_id_to_check = event_update.animal_id if event_update.animal_id else db_event.animal_id
    if animal_id_to_check:
        animal_to_check = await crud_animal.get(db, id=animal_id_to_check)
        if animal_to_check:
            is_animal_owner = animal_to_check.owner_user_id == current_user.id
            has_animal_farm_access = False
            if not is_animal_owner and animal_to_check.current_lot and animal_to_check.current_lot.farm:
                user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
                user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
                all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

                if animal_to_check.current_lot.farm.id in all_accessible_farm_ids:
                    has_animal_farm_access = True
            
            if is_animal_owner or has_animal_farm_access:
                is_authorized = True
            else: # If trying to change to an unauthorized animal
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to use animal with ID '{animal_id_to_check}'.")
        elif event_update.animal_id: # If new animal_id provided but not found
            raise HTTPException(status_code=400, detail=f"Animal with ID '{event_update.animal_id}' not found for update.")

    # Check access to the sire animal (current or new if updated)
    sire_animal_id_to_check = event_update.sire_animal_id if event_update.sire_animal_id else db_event.sire_animal_id
    if not is_authorized and sire_animal_id_to_check: # Only check sire if not already authorized by female
        sire_animal_to_check = await crud_animal.get(db, id=sire_animal_id_to_check)
        if sire_animal_to_check:
            is_sire_owner = sire_animal_to_check.owner_user_id == current_user.id
            has_sire_farm_access = False
            if not is_sire_owner and sire_animal_to_check.current_lot and sire_animal_to_check.current_lot.farm:
                user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
                user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
                all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

                if sire_animal_to_check.current_lot.farm.id in all_accessible_farm_ids:
                    has_sire_farm_access = True
            
            if is_sire_owner or has_sire_farm_access:
                is_authorized = True
            else: # If trying to change to an unauthorized sire
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to use sire animal with ID '{sire_animal_id_to_check}'.")
        elif event_update.sire_animal_id: # If new sire_animal_id provided but not found
            raise HTTPException(status_code=400, detail=f"Sire animal with ID '{event_update.sire_animal_id}' not found for update.")

    if not is_authorized: # Final check if no authorization was granted by any animal
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this reproductive event.")

    try:
        updated_event = await crud_reproductive_event.update(db, db_obj=db_event, obj_in=event_update)
        if updated_event is None:
            raise HTTPException(status_code=500, detail="Failed to update reproductive event unexpectedly.") 
        return updated_event
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_reproductive_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Elimina un evento reproductivo específico.
    Solo accesible si el usuario es propietario de la hembra o el semental involucrado,
    o tiene acceso a la finca de alguno de ellos.
    """
    db_event = await crud_reproductive_event.get(db, id=event_id)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Reproductive event not found")
    
    is_authorized = False

    # Check access to the female animal
    if db_event.animal:
        is_animal_owner = db_event.animal.owner_user_id == current_user.id
        has_animal_farm_access = False
        if not is_animal_owner and db_event.animal.current_lot and db_event.animal.current_lot.farm:
            user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
            user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
            all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

            if db_event.animal.current_lot.farm.id in all_accessible_farm_ids:
                has_animal_farm_access = True
        
        if is_animal_owner or has_animal_farm_access:
            is_authorized = True

    # Check access to the sire animal if exists and not already authorized
    if not is_authorized and db_event.sire_animal:
        is_sire_owner = db_event.sire_animal.owner_user_id == current_user.id
        has_sire_farm_access = False
        if not is_sire_owner and db_event.sire_animal.current_lot and db_event.sire_animal.current_lot.farm:
            user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
            user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
            all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

            if db_event.sire_animal.current_lot.farm.id in all_accessible_farm_ids:
                has_sire_farm_access = True
        
        if is_sire_owner or has_sire_farm_access:
            is_authorized = True

    if not is_authorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this reproductive event.")
    
    deleted_event = await crud_reproductive_event.remove(db, id=event_id)
    if not deleted_event:
        raise HTTPException(status_code=500, detail="Failed to delete reproductive event unexpectedly.")
    return Response(status_code=status.HTTP_204_NO_CONTENT) # Retorno correcto para 204

# --- Rutas para OffspringBorn (crías nacidas) ---
@router.post("/offspring-born/", response_model=schemas.OffspringBorn, status_code=status.HTTP_201_CREATED)
async def create_new_offspring_born(
    offspring_in: schemas.OffspringBornCreate, # Renombrado
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Registra una nueva cría nacida de un evento reproductivo.
    Se valida que el evento reproductivo existe y que el usuario tiene permisos sobre él.
    Se valida que la cría exista y pertenezca al usuario (o su finca).
    """
    db_event = await crud_reproductive_event.get(db, id=offspring_in.reproductive_event_id)
    if not db_event:
        raise HTTPException(status_code=400, detail=f"Reproductive event with ID '{offspring_in.reproductive_event_id}' not found.")
    
    # Lógica de autorización sobre el evento reproductivo (verificar que el usuario tenga acceso a la hembra/semental)
    is_event_authorized = False
    
    if db_event.animal:
        is_animal_owner = db_event.animal.owner_user_id == current_user.id
        has_animal_farm_access = False
        if not is_animal_owner and db_event.animal.current_lot and db_event.animal.current_lot.farm:
            user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
            user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
            all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

            if db_event.animal.current_lot.farm.id in all_accessible_farm_ids:
                has_animal_farm_access = True
        
        if is_animal_owner or has_animal_farm_access:
            is_event_authorized = True

    if not is_event_authorized and db_event.sire_animal:
        is_sire_owner = db_event.sire_animal.owner_user_id == current_user.id
        has_sire_farm_access = False
        if not is_sire_owner and db_event.sire_animal.current_lot and db_event.sire_animal.current_lot.farm:
            user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
            user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
            all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

            if db_event.sire_animal.current_lot.farm.id in all_accessible_farm_ids:
                has_sire_farm_access = True
        
        if is_sire_owner or has_sire_farm_access:
            is_event_authorized = True

    if not is_event_authorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to add offspring to this reproductive event.")

    # Validar que la cría (offspring_animal_id) exista y pertenezca al usuario o a su finca
    offspring_animal_db = await crud_animal.get(db, id=offspring_in.offspring_animal_id)
    if not offspring_animal_db:
        raise HTTPException(status_code=400, detail=f"Offspring animal with ID '{offspring_in.offspring_animal_id}' not found.")
    
    is_offspring_owner = offspring_animal_db.owner_user_id == current_user.id
    has_offspring_farm_access = False
    if not is_offspring_owner and offspring_animal_db.current_lot:
        user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
        user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
        all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

        if offspring_animal_db.current_lot.farm and offspring_animal_db.current_lot.farm.id in all_accessible_farm_ids:
            has_offspring_farm_access = True
    
    if not (is_offspring_owner or has_offspring_farm_access):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to link offspring animal with ID '{offspring_in.offspring_animal_id}'.")

    try:
        db_offspring_born = await crud_offspring_born.create(db=db, obj_in=offspring_in, born_by_user_id=current_user.id)
        return db_offspring_born
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/offspring-born/{offspring_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_offspring_born(
    offspring_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Elimina un registro de cría nacida.
    Solo accesible si el usuario tiene permisos sobre el evento reproductivo asociado.
    """
    db_offspring_born = await crud_offspring_born.get(db, id=offspring_id)
    if db_offspring_born is None:
        raise HTTPException(status_code=404, detail="Offspring born record not found.")

    # Re-validar permisos sobre el evento reproductivo asociado (asumiendo que está cargado)
    db_event = await crud_reproductive_event.get(db, id=db_offspring_born.reproductive_event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Associated reproductive event not found.")

    is_event_authorized = False
    if db_event.animal:
        is_animal_owner = db_event.animal.owner_user_id == current_user.id
        has_animal_farm_access = False
        if not is_animal_owner and db_event.animal.current_lot and db_event.animal.current_lot.farm:
            user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
            user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
            all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

            if db_event.animal.current_lot.farm.id in all_accessible_farm_ids:
                has_animal_farm_access = True
        
        if is_animal_owner or has_animal_farm_access:
            is_event_authorized = True

    if not is_event_authorized and db_event.sire_animal:
        is_sire_owner = db_event.sire_animal.owner_user_id == current_user.id
        has_sire_farm_access = False
        if not is_sire_owner and db_event.sire_animal.current_lot and db_event.sire_animal.current_lot.farm:
            user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
            user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
            all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

            if db_event.sire_animal.current_lot.farm.id in all_accessible_farm_ids:
                has_sire_farm_access = True
        
        if is_sire_owner or has_sire_farm_access:
            is_event_authorized = True

    if not is_event_authorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete offspring from this reproductive event.")
    
    deleted_offspring = await crud_offspring_born.remove(db, id=offspring_id)
    if not deleted_offspring:
        raise HTTPException(status_code=500, detail="Failed to delete offspring born record unexpectedly.")
    return Response(status_code=status.HTTP_204_NO_CONTENT) # Retorno correcto para 204

