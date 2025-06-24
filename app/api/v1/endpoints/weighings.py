# routers/weighings.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid

# --- Importaciones de módulos centrales ---
from app import crud, schemas, models # Acceso de alto nivel a tus módulos principales

# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI (get_db, get_current_user, etc.)

router = APIRouter(
    prefix="/weighings",
    tags=["Weighings"],
    responses={404: {"description": "Not found"}},
)

# --- Rutas de Pesajes ---

@router.post("/", response_model=schemas.Weighing, status_code=status.HTTP_201_CREATED)
async def create_new_weighing(
    weighing: schemas.WeighingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Crea un nuevo registro de pesaje para un animal.
    Se valida que el animal existe y es accesible por el usuario.
    """
    animal_db = await crud.get_animal(db, weighing.animal_id)
    if not animal_db:
        raise HTTPException(status_code=400, detail=f"Animal with ID '{weighing.animal_id}' not found.")
    
    # Lógica de autorización: el usuario debe ser propietario del animal
    if str(animal_db.owner_user_id) != str(current_user.id):
        if animal_db.current_lot:
            if not animal_db.current_lot.farm or str(animal_db.current_lot.farm.owner_user_id) != str(current_user.id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to add weighing for animal with ID '{weighing.animal_id}'.")
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to add weighing for animal with ID '{weighing.animal_id}'.")

    try:
        db_weighing = await crud.create_weighing(db=db, weighing=weighing)
        return db_weighing
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{weighing_id}", response_model=schemas.Weighing)
async def read_weighing(
    weighing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene los detalles de un registro de pesaje específico.
    Solo accesible si el usuario es propietario del animal asociado.
    """
    db_weighing = await crud.get_weighing(db, weighing_id=weighing_id)
    if db_weighing is None:
        raise HTTPException(status_code=404, detail="Weighing record not found")
    
    # Lógica de autorización: el usuario debe ser propietario del animal asociado
    # Animal está lazy="selectin" en Weighing.
    if not db_weighing.animal or str(db_weighing.animal.owner_user_id) != str(current_user.id):
        # TODO: También verificar si el usuario tiene acceso a la finca del animal.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this weighing record.")
    
    return db_weighing

@router.get("/", response_model=List[schemas.Weighing])
async def read_weighings(
    animal_id: Optional[uuid.UUID] = None, # Filtrar por animal
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene una lista de registros de pesajes, opcionalmente filtrados por animal.
    Solo muestra pesajes de animales que el usuario posee o a cuyas fincas tiene acceso.
    """
    authorized_animal_ids = set()
    user_animals = await crud.get_animals(db, owner_id=current_user.id)
    authorized_animal_ids.update({a.id for a in user_animals})

    user_farms = await crud.get_farms(db, owner_id=current_user.id)
    for farm in user_farms:
        farm_animals = await crud.get_animals(db, farm_id=farm.id)
        authorized_animal_ids.update({a.id for a in farm_animals})

    if animal_id:
        if animal_id not in authorized_animal_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to list weighings for this animal.")
        weighings = await crud.get_weighings_by_animal(db, animal_id=animal_id, skip=skip, limit=limit)
    else:
        # Obtener todos los pesajes y luego filtrar por animales autorizados
        all_weighings = await crud.get_weighings(db, skip=0, limit=None)
        weighings = [
            w for w in all_weighings 
            if w.animal_id in authorized_animal_ids
        ][skip : skip + limit]

    return weighings

@router.put("/{weighing_id}", response_model=schemas.Weighing)
async def update_existing_weighing(
    weighing_id: uuid.UUID,
    weighing_update: schemas.WeighingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Actualiza los detalles de un registro de pesaje específico.
    Solo el propietario del animal asociado puede actualizarlo.
    """
    db_weighing = await crud.get_weighing(db, weighing_id=weighing_id)
    if db_weighing is None:
        raise HTTPException(status_code=404, detail="Weighing record not found")
    
    if not db_weighing.animal or str(db_weighing.animal.owner_user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this weighing record.")

    # Si se intenta cambiar el animal_id, validar el nuevo animal
    if weighing_update.animal_id and weighing_update.animal_id != db_weighing.animal_id:
        new_animal_db = await crud.get_animal(db, weighing_update.animal_id)
        if not new_animal_db:
            raise HTTPException(status_code=400, detail=f"New animal with ID '{weighing_update.animal_id}' not found.")
        if str(new_animal_db.owner_user_id) != str(current_user.id):
            if new_animal_db.current_lot:
                if not new_animal_db.current_lot.farm or str(new_animal_db.current_lot.farm.owner_user_id) != str(current_user.id):
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to move weighing to new animal with ID '{weighing_update.animal_id}'.")
            else:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to move weighing to new animal with ID '{weighing_update.animal_id}'.")

    try:
        updated_weighing = await crud.update_weighing(db, weighing_id, weighing_update)
        if updated_weighing is None:
            raise HTTPException(status_code=500, detail="Failed to update weighing record unexpectedly.") 
        return updated_weighing
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{weighing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_weighing(
    weighing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Elimina un registro de pesaje específico.
    Solo el propietario del animal asociado puede eliminarlo.
    """
    db_weighing = await crud.get_weighing(db, weighing_id=weighing_id)
    if db_weighing is None:
        raise HTTPException(status_code=404, detail="Weighing record not found")
    
    if not db_weighing.animal or str(db_weighing.animal.owner_user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this weighing record.")
    
    try:
        deleted = await crud.delete_weighing(db, weighing_id)
        if not deleted:
            raise HTTPException(status_code=500, detail="Failed to delete weighing record unexpectedly.")
        return {"message": "Weighing record deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

