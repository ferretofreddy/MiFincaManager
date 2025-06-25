# app/api/v1/endpoints/farms.py
from fastapi import APIRouter, Depends, HTTPException, status, Response # Importa Response
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List

# --- Importaciones de módulos centrales ---
from app import schemas, models
from app.crud import farm as crud_farm # Importa la instancia CRUD para farm

# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI

# Asumiendo que 'get_db' y 'get_current_user' estarán en 'app/api/deps.py'
get_db = deps.get_db
get_current_user = deps.get_current_user
get_current_active_user = deps.get_current_active_user
get_current_active_superuser = deps.get_current_active_superuser # Para superusuarios

router = APIRouter(
    prefix="/farms",
    tags=["Farms"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Farm, status_code=status.HTTP_201_CREATED)
async def create_new_farm(
    farm_in: schemas.FarmCreate, # Renombrado a farm_in para claridad con la instancia farm
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user) # Solo usuarios activos pueden crear fincas
):
    """
    Crea una nueva finca para el usuario autenticado.
    """
    # Usar la instancia crud.farm
    return await crud_farm.create(db=db, obj_in=farm_in, owner_user_id=current_user.id)

@router.get("/{farm_id}", response_model=schemas.Farm)
async def read_farm(
    farm_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user) # Solo usuarios activos pueden leer fincas
):
    """
    Obtiene una finca por su ID. Solo si el usuario autenticado es el propietario.
    """
    db_farm = await crud_farm.get(db, id=farm_id) # Usar crud.farm.get
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
    current_user: models.User = Depends(get_current_active_user) # Solo usuarios activos pueden listar sus fincas
):
    """
    Obtiene una lista de fincas del usuario autenticado.
    """
    # Usar la función que filtra por owner_id de crud.farm
    farms = await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id, skip=skip, limit=limit)
    return farms

@router.put("/{farm_id}", response_model=schemas.Farm)
async def update_existing_farm(
    farm_id: uuid.UUID,
    farm_update: schemas.FarmUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user) # Solo usuarios activos pueden actualizar fincas
):
    """
    Actualiza una finca existente por su ID. Solo si el usuario autenticado es el propietario.
    """
    db_farm = await crud_farm.get(db, id=farm_id) # Usar crud.farm.get
    if db_farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    if db_farm.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this farm."
        )
    
    updated_farm = await crud_farm.update(db, db_obj=db_farm, obj_in=farm_update) # Usar crud.farm.update
    return updated_farm

@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_farm(
    farm_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user) # Solo usuarios activos pueden eliminar fincas
):
    """
    Elimina una finca por su ID. Solo si el usuario autenticado es el propietario.
    """
    db_farm = await crud_farm.get(db, id=farm_id) # Usar crud.farm.get
    if db_farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    if db_farm.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this farm."
        )
    
    deleted_farm = await crud_farm.remove(db, id=farm_id) # Usar crud.farm.remove
    if not deleted_farm: # crud.remove ya devuelve el objeto eliminado o None
        raise HTTPException(status_code=404, detail="Farm not found or could not be deleted")
    return Response(status_code=status.HTTP_204_NO_CONTENT) # Retorno correcto para 204

