# routers/farms.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List

# --- Importaciones de módulos centrales ---
from app import crud, schemas, models # Acceso de alto nivel a tus módulos principales

# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI (get_db, get_current_user, etc.)

router = APIRouter(
    prefix="/farms",
    tags=["Farms"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Farm, status_code=status.HTTP_201_CREATED)
async def create_new_farm(
    farm: schemas.FarmCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Crea una nueva finca para el usuario autenticado.
    """
    return await crud.create_farm(db=db, farm=farm, owner_user_id=current_user.id)

@router.get("/{farm_id}", response_model=schemas.Farm)
async def read_farm(
    farm_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene una finca por su ID. Solo si el usuario autenticado es el propietario.
    """
    db_farm = await crud.get_farm(db, farm_id=farm_id)
    if db_farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    if db_farm.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this farm."
        )
    return db_farm

@router.get("/", response_model=List[schemas.Farm])
async def read_farms(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene una lista de fincas del usuario autenticado.
    """
    # Usar la función que filtra por owner_id
    farms = await crud.get_farms_by_owner_id(db, owner_user_id=current_user.id, skip=skip, limit=limit)
    return farms

@router.put("/{farm_id}", response_model=schemas.Farm)
async def update_existing_farm(
    farm_id: uuid.UUID,
    farm_update: schemas.FarmUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Actualiza una finca existente por su ID. Solo si el usuario autenticado es el propietario.
    """
    db_farm = await crud.get_farm(db, farm_id=farm_id)
    if db_farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    if db_farm.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this farm."
        )
    
    updated_farm = await crud.update_farm(db, farm_id=farm_id, farm_update=farm_update)
    return updated_farm

@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_farm(
    farm_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Elimina una finca por su ID. Solo si el usuario autenticado es el propietario.
    """
    db_farm = await crud.get_farm(db, farm_id=farm_id)
    if db_farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    if db_farm.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this farm."
        )
    
    success = await crud.delete_farm(db, farm_id=farm_id)
    if not success:
        raise HTTPException(status_code=404, detail="Farm not found or could not be deleted")
    return {"message": "Farm deleted successfully"}

