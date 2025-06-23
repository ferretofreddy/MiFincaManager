# routers/feedings.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid

from database import get_db
import schemas
import crud
from dependencies import get_current_user 
import models # Para los modelos ORM

router = APIRouter(
    prefix="/feedings",
    tags=["Feedings"],
    responses={404: {"description": "Not found"}},
)

# --- Rutas de Alimentación ---

@router.post("/", response_model=schemas.Feeding, status_code=status.HTTP_201_CREATED)
async def create_new_feeding(
    feeding: schemas.FeedingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Crea un nuevo registro de alimentación y lo asocia a los animales proporcionados.
    Se valida si el tipo de alimento y suplemento (si aplica) existen en MasterData.
    Se valida que los animales existen y son accesibles por el usuario.
    """
    if feeding.feed_type_id:
        feed_type_data = await crud.get_master_data(db, feeding.feed_type_id)
        if not feed_type_data:
            raise HTTPException(status_code=400, detail=f"Feed type with ID '{feeding.feed_type_id}' not found in MasterData.")
        # Opcional: Verificar que la categoría sea 'feed_type'
        # if feed_type_data.category != 'feed_type':
        #     raise HTTPException(status_code=400, detail="Provided feed_type_id is not of category 'feed_type'.")

    if feeding.supplement_id:
        supplement_data = await crud.get_master_data(db, feeding.supplement_id)
        if not supplement_data:
            raise HTTPException(status_code=400, detail=f"Supplement with ID '{feeding.supplement_id}' not found in MasterData.")
        # Opcional: Verificar que la categoría sea 'supplement'
        # if supplement_data.category != 'supplement':
        #     raise HTTPException(status_code=400, detail="Provided supplement_id is not of category 'supplement'.")

    # Validar que los animales existen y pertenecen al usuario o a sus fincas
    for animal_id in feeding.animal_ids:
        animal = await crud.get_animal(db, animal_id)
        if not animal:
            raise HTTPException(status_code=400, detail=f"Animal with ID '{animal_id}' not found.")
        
        # Lógica de autorización para cada animal
        if str(animal.owner_user_id) != str(current_user.id):
            if animal.current_lot:
                if not animal.current_lot.farm or str(animal.current_lot.farm.owner_user_id) != str(current_user.id):
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to assign feeding to animal with ID '{animal_id}'.")
            else:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to assign feeding to animal with ID '{animal_id}'.")

    try:
        db_feeding = await crud.create_feeding(db=db, feeding=feeding, 
                                            administered_by_user_id=current_user.id)
        return db_feeding
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{feeding_id}", response_model=schemas.Feeding)
async def read_feeding(
    feeding_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene los detalles de un registro de alimentación específico.
    Solo accesible si el usuario administró el evento o es propietario de los animales afectados.
    """
    db_feeding = await crud.get_feeding(db, feeding_id=feeding_id)
    if db_feeding is None:
        raise HTTPException(status_code=404, detail="Feeding record not found")
    
    # Lógica de autorización: el usuario debe haber administrado el evento
    if str(db_feeding.administered_by_user_id) != str(current_user.id):
        # TODO: También verificar si el usuario tiene acceso a *al menos uno* de los animales afectados.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this feeding record.")
    
    return db_feeding

@router.get("/", response_model=List[schemas.Feeding])
async def read_feedings(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene una lista de registros de alimentación.
    Solo muestra eventos administrados por el usuario actual.
    """
    feedings = await crud.get_feedings(db, skip=skip, limit=limit)
    user_feedings = [f for f in feedings if str(f.administered_by_user_id) == str(current_user.id)]
    return user_feedings

@router.put("/{feeding_id}", response_model=schemas.Feeding)
async def update_existing_feeding(
    feeding_id: uuid.UUID,
    feeding_update: schemas.FeedingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Actualiza los detalles de un registro de alimentación específico.
    Solo el usuario que lo administró puede actualizarlo.
    """
    db_feeding = await crud.get_feeding(db, feeding_id=feeding_id)
    if db_feeding is None:
        raise HTTPException(status_code=404, detail="Feeding record not found")
    
    if str(db_feeding.administered_by_user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this feeding record.")

    if feeding_update.feed_type_id:
        feed_type_data = await crud.get_master_data(db, feeding_update.feed_type_id)
        if not feed_type_data:
            raise HTTPException(status_code=400, detail=f"Feed type with ID '{feeding_update.feed_type_id}' not found in MasterData.")

    if feeding_update.supplement_id:
        supplement_data = await crud.get_master_data(db, feeding_update.supplement_id)
        if not supplement_data:
            raise HTTPException(status_code=400, detail=f"Supplement with ID '{feeding_update.supplement_id}' not found in MasterData.")

    try:
        updated_feeding = await crud.update_feeding(db, feeding_id, feeding_update)
        if updated_feeding is None:
            raise HTTPException(status_code=500, detail="Failed to update feeding record unexpectedly.") 
        return updated_feeding
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{feeding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_feeding(
    feeding_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Elimina un registro de alimentación específico.
    Solo el usuario que lo administró puede eliminarlo.
    """
    db_feeding = await crud.get_feeding(db, feeding_id=feeding_id)
    if db_feeding is None:
        raise HTTPException(status_code=404, detail="Feeding record not found")
    
    if str(db_feeding.administered_by_user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this feeding record.")
    
    try:
        deleted = await crud.delete_feeding(db, feeding_id)
        if not deleted:
            raise HTTPException(status_code=500, detail="Failed to delete feeding record unexpectedly.")
        return {"message": "Feeding record deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

