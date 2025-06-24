# routers/reproductive_events.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid

# --- Importaciones de módulos centrales ---
from app import crud, schemas, models # Acceso de alto nivel a tus módulos principales

# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI (get_db, get_current_user, etc.)

router = APIRouter(
    prefix="/reproductive-events",
    tags=["Reproductive Events"],
    responses={404: {"description": "Not found"}},
)

# --- Rutas de Eventos Reproductivos ---

@router.post("/", response_model=schemas.ReproductiveEvent, status_code=status.HTTP_201_CREATED)
async def create_new_reproductive_event(
    event: schemas.ReproductiveEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Crea un nuevo evento reproductivo.
    Se valida que el animal (hembra) y el semental (si aplica) existen y son accesibles.
    """
    # Validar que el animal existe y pertenece al usuario o su finca
    animal_db = await crud.get_animal(db, event.animal_id)
    if not animal_db:
        raise HTTPException(status_code=400, detail=f"Animal with ID '{event.animal_id}' not found.")
    # Si el animal no es del usuario, verificar acceso a la finca del animal
    if str(animal_db.owner_user_id) != str(current_user.id):
        if animal_db.current_lot:
            if not animal_db.current_lot.farm or str(animal_db.current_lot.farm.owner_user_id) != str(current_user.id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to create reproductive event for animal with ID '{event.animal_id}'.")
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to create reproductive event for animal with ID '{event.animal_id}'.")

    # Validar que si hay semental, exista y sea accesible
    if event.sire_animal_id:
        sire_animal_db = await crud.get_animal(db, event.sire_animal_id)
        if not sire_animal_db:
            raise HTTPException(status_code=400, detail=f"Sire animal with ID '{event.sire_animal_id}' not found.")
        # Si el semental no es del usuario, verificar acceso a la finca del semental
        if str(sire_animal_db.owner_user_id) != str(current_user.id):
            if sire_animal_db.current_lot:
                if not sire_animal_db.current_lot.farm or str(sire_animal_db.current_lot.farm.owner_user_id) != str(current_user.id):
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to use sire animal with ID '{event.sire_animal_id}'.")
            else:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to use sire animal with ID '{event.sire_animal_id}'.")

    try:
        db_event = await crud.create_reproductive_event(db=db, event=event)
        return db_event
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{event_id}", response_model=schemas.ReproductiveEvent)
async def read_reproductive_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene los detalles de un evento reproductivo específico.
    Solo accesible si el usuario es propietario de la hembra o el semental involucrado.
    """
    db_event = await crud.get_reproductive_event(db, event_id=event_id)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Reproductive event not found")
    
    # Lógica de autorización: el usuario debe ser propietario del animal (hembra)
    # o tener acceso a la finca de la hembra. También debería aplicar para el semental.
    is_authorized = False
    if db_event.animal and str(db_event.animal.owner_user_id) == str(current_user.id):
        is_authorized = True
    elif db_event.animal and db_event.animal.current_lot and db_event.animal.current_lot.farm and str(db_event.animal.current_lot.farm.owner_user_id) == str(current_user.id):
        is_authorized = True
    
    # Si hay semental, también verificar su propiedad/acceso
    if not is_authorized and db_event.sire_animal:
        if str(db_event.sire_animal.owner_user_id) == str(current_user.id):
            is_authorized = True
        elif db_event.sire_animal.current_lot and db_event.sire_animal.current_lot.farm and str(db_event.sire_animal.current_lot.farm.owner_user_id) == str(current_user.id):
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
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene una lista de eventos reproductivos, opcionalmente filtrados por animal (hembra).
    Solo muestra eventos relacionados con animales que el usuario posee o a cuyas fincas tiene acceso.
    """
    # Lógica de autorización: solo los eventos de animales que el usuario posee o tiene acceso
    authorized_animal_ids = set()
    user_animals = await crud.get_animals(db, owner_id=current_user.id)
    authorized_animal_ids.update({a.id for a in user_animals})

    user_farms = await crud.get_farms(db, owner_id=current_user.id)
    for farm in user_farms:
        farm_animals = await crud.get_animals(db, farm_id=farm.id)
        authorized_animal_ids.update({a.id for a in farm_animals})

    # Si se filtra por un animal específico, validar que sea uno autorizado
    if animal_id:
        if animal_id not in authorized_animal_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to list reproductive events for this animal.")
        events = await crud.get_reproductive_events(db, animal_id=animal_id, skip=skip, limit=limit)
    else:
        # Si no se filtra por animal específico, obtener todos los eventos y luego filtrar
        all_events = await crud.get_reproductive_events(db, skip=0, limit=None) # Obtener todos los eventos
        events = [
            event for event in all_events 
            if event.animal_id in authorized_animal_ids or 
               (event.sire_animal_id and event.sire_animal_id in authorized_animal_ids)
        ][skip : skip + limit] # Aplicar paginación después del filtro

    return events


@router.put("/{event_id}", response_model=schemas.ReproductiveEvent)
async def update_existing_reproductive_event(
    event_id: uuid.UUID,
    event_update: schemas.ReproductiveEventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Actualiza los detalles de un evento reproductivo específico.
    Solo accesible si el usuario es propietario de la hembra o el semental involucrado.
    """
    db_event = await crud.get_reproductive_event(db, event_id=event_id)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Reproductive event not found")
    
    is_authorized = False
    if db_event.animal and str(db_event.animal.owner_user_id) == str(current_user.id):
        is_authorized = True
    elif db_event.animal and db_event.animal.current_lot and db_event.animal.current_lot.farm and str(db_event.animal.current_lot.farm.owner_user_id) == str(current_user.id):
        is_authorized = True
    
    if not is_authorized and db_event.sire_animal:
        if str(db_event.sire_animal.owner_user_id) == str(current_user.id):
            is_authorized = True
        elif db_event.sire_animal.current_lot and db_event.sire_animal.current_lot.farm and str(db_event.sire_animal.current_lot.farm.owner_user_id) == str(current_user.id):
            is_authorized = True

    if not is_authorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this reproductive event.")

    # Validar si se cambia el animal o semental
    if event_update.animal_id and event_update.animal_id != db_event.animal_id:
        animal_db = await crud.get_animal(db, event_update.animal_id)
        if not animal_db:
            raise HTTPException(status_code=400, detail=f"New animal with ID '{event_update.animal_id}' not found.")
        if str(animal_db.owner_user_id) != str(current_user.id):
            if animal_db.current_lot:
                if not animal_db.current_lot.farm or str(animal_db.current_lot.farm.owner_user_id) != str(current_user.id):
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to use new animal with ID '{event_update.animal_id}'.")
            else:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to use new animal with ID '{event_update.animal_id}'.")

    if event_update.sire_animal_id and event_update.sire_animal_id != db_event.sire_animal_id:
        sire_animal_db = await crud.get_animal(db, event_update.sire_animal_id)
        if not sire_animal_db:
            raise HTTPException(status_code=400, detail=f"New sire animal with ID '{event_update.sire_animal_id}' not found.")
        if str(sire_animal_db.owner_user_id) != str(current_user.id):
            if sire_animal_db.current_lot:
                if not sire_animal_db.current_lot.farm or str(sire_animal_db.current_lot.farm.owner_user_id) != str(current_user.id):
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to use new sire animal with ID '{event_update.sire_animal_id}'.")
            else:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to use new sire animal with ID '{event_update.sire_animal_id}'.")

    try:
        updated_event = await crud.update_reproductive_event(db, event_id, event_update)
        if updated_event is None:
            raise HTTPException(status_code=500, detail="Failed to update reproductive event unexpectedly.") 
        return updated_event
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_reproductive_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Elimina un evento reproductivo específico.
    Solo accesible si el usuario es propietario de la hembra o el semental involucrado.
    """
    db_event = await crud.get_reproductive_event(db, event_id=event_id)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Reproductive event not found")
    
    is_authorized = False
    if db_event.animal and str(db_event.animal.owner_user_id) == str(current_user.id):
        is_authorized = True
    elif db_event.animal and db_event.animal.current_lot and db_event.animal.current_lot.farm and str(db_event.animal.current_lot.farm.owner_user_id) == str(current_user.id):
        is_authorized = True
    
    if not is_authorized and db_event.sire_animal:
        if str(db_event.sire_animal.owner_user_id) == str(current_user.id):
            is_authorized = True
        elif db_event.sire_animal.current_lot and db_event.sire_animal.current_lot.farm and str(db_event.sire_animal.current_lot.farm.owner_user_id) == str(current_user.id):
            is_authorized = True

    if not is_authorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this reproductive event.")
    
    try:
        deleted = await crud.delete_reproductive_event(db, event_id)
        if not deleted:
            raise HTTPException(status_code=500, detail="Failed to delete reproductive event unexpectedly.")
        return {"message": "Reproductive event deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Rutas para OffspringBorn (crías nacidas) ---
@router.post("/offspring-born/", response_model=schemas.OffspringBorn, status_code=status.HTTP_201_CREATED)
async def create_new_offspring_born(
    offspring: schemas.OffspringBornCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Registra una nueva cría nacida de un evento reproductivo.
    Se valida que el evento reproductivo existe y que el usuario tiene permisos sobre él.
    Se valida que la cría exista y pertenezca al usuario (o su finca).
    """
    db_event = await crud.get_reproductive_event(db, offspring.reproductive_event_id)
    if not db_event:
        raise HTTPException(status_code=400, detail=f"Reproductive event with ID '{offspring.reproductive_event_id}' not found.")
    
    # Lógica de autorización sobre el evento reproductivo (verificar que el usuario tenga acceso a la hembra/semental)
    is_event_authorized = False
    if db_event.animal and str(db_event.animal.owner_user_id) == str(current_user.id):
        is_event_authorized = True
    elif db_event.animal and db_event.animal.current_lot and db_event.animal.current_lot.farm and str(db_event.animal.current_lot.farm.owner_user_id) == str(current_user.id):
        is_event_authorized = True
    
    if not is_event_authorized and db_event.sire_animal:
        if str(db_event.sire_animal.owner_user_id) == str(current_user.id):
            is_event_authorized = True
        elif db_event.sire_animal.current_lot and db_event.sire_animal.current_lot.farm and str(db_event.sire_animal.current_lot.farm.owner_user_id) == str(current_user.id):
            is_event_authorized = True

    if not is_event_authorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to add offspring to this reproductive event.")

    # Validar que la cría (offspring_animal_id) exista y pertenezca al usuario
    offspring_animal_db = await crud.get_animal(db, offspring.offspring_animal_id)
    if not offspring_animal_db:
        raise HTTPException(status_code=400, detail=f"Offspring animal with ID '{offspring.offspring_animal_id}' not found.")
    
    if str(offspring_animal_db.owner_user_id) != str(current_user.id):
        if offspring_animal_db.current_lot:
            if not offspring_animal_db.current_lot.farm or str(offspring_animal_db.current_lot.farm.owner_user_id) != str(current_user.id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to link offspring animal with ID '{offspring.offspring_animal_id}'.")
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to link offspring animal with ID '{offspring.offspring_animal_id}'.")

    try:
        db_offspring_born = await crud.create_offspring_born(db=db, offspring=offspring)
        return db_offspring_born
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/offspring-born/{offspring_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_offspring_born(
    offspring_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Elimina un registro de cría nacida.
    Solo accesible si el usuario tiene permisos sobre el evento reproductivo asociado.
    """
    db_offspring_born = await crud.get_offspring_born(db, offspring_id=offspring_id)
    if db_offspring_born is None:
        raise HTTPException(status_code=404, detail="Offspring born record not found.")

    # Re-validar permisos sobre el evento reproductivo asociado (asumiendo que está cargado)
    db_event = await crud.get_reproductive_event(db, db_offspring_born.reproductive_event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Associated reproductive event not found.")

    is_event_authorized = False
    if db_event.animal and str(db_event.animal.owner_user_id) == str(current_user.id):
        is_event_authorized = True
    elif db_event.animal and db_event.animal.current_lot and db_event.animal.current_lot.farm and str(db_event.animal.current_lot.farm.owner_user_id) == str(current_user.id):
        is_event_authorized = True
    
    if not is_event_authorized and db_event.sire_animal:
        if str(db_event.sire_animal.owner_user_id) == str(current_user.id):
            is_event_authorized = True
        elif db_event.sire_animal.current_lot and db_event.sire_animal.current_lot.farm and str(db_event.sire_animal.current_lot.farm.owner_user_id) == str(current_user.id):
            is_event_authorized = True

    if not is_event_authorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete offspring from this reproductive event.")
    
    try:
        deleted = await crud.delete_offspring_born(db, offspring_id)
        if not deleted:
            raise HTTPException(status_code=500, detail="Failed to delete offspring born record unexpectedly.")
        return {"message": "Offspring born record deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
