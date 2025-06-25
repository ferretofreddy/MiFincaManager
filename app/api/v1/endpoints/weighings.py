# app/api/v1/endpoints/weighings.py
from fastapi import APIRouter, Depends, HTTPException, status, Response # Importa Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid

# --- Importaciones de módulos centrales ---
from app import schemas, models
from app.crud import weighing as crud_weighing
from app.crud import animal as crud_animal
from app.crud import user_farm_access as crud_user_farm_access
from app.crud import farm as crud_farm


# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI

get_db = deps.get_db
get_current_active_user = deps.get_current_active_user


router = APIRouter(
    prefix="/weighings",
    tags=["Weighings"],
    responses={404: {"description": "Not found"}},
)

# --- Rutas de Pesajes ---

@router.post("/", response_model=schemas.Weighing, status_code=status.HTTP_201_CREATED)
async def create_new_weighing(
    weighing_in: schemas.WeighingCreate, # Renombrado
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Crea un nuevo registro de pesaje para un animal.
    Se valida que el animal existe y es accesible por el usuario.
    """
    animal_db = await crud_animal.get(db, id=weighing_in.animal_id)
    if not animal_db:
        raise HTTPException(status_code=400, detail=f"Animal with ID '{weighing_in.animal_id}' not found.")
    
    # Lógica de autorización: el usuario debe ser propietario del animal o tener acceso a su finca
    is_animal_owner = animal_db.owner_user_id == current_user.id
    has_animal_farm_access = False
    if not is_animal_owner and animal_db.current_lot:
        user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
        user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
        all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

        if animal_db.current_lot.farm and animal_db.current_lot.farm.id in all_accessible_farm_ids:
            has_animal_farm_access = True
    
    if not (is_animal_owner or has_animal_farm_access):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to add weighing for animal with ID '{weighing_in.animal_id}'.")

    try:
        db_weighing = await crud_weighing.create(db=db, obj_in=weighing_in, recorded_by_user_id=current_user.id) # Pasa recorded_by_user_id
        return db_weighing
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{weighing_id}", response_model=schemas.Weighing)
async def read_weighing(
    weighing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtiene los detalles de un registro de pesaje específico.
    Solo accesible si el usuario es propietario del animal asociado o tiene acceso a su finca.
    """
    db_weighing = await crud_weighing.get(db, id=weighing_id)
    if db_weighing is None:
        raise HTTPException(status_code=404, detail="Weighing record not found")
    
    # Lógica de autorización: el usuario debe ser propietario del animal asociado o tener acceso a su finca.
    is_animal_owner = db_weighing.animal.owner_user_id == current_user.id
    has_animal_farm_access = False
    if not is_animal_owner and db_weighing.animal.current_lot:
        user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
        user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
        all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

        if db_weighing.animal.current_lot.farm and db_weighing.animal.current_lot.farm.id in all_accessible_farm_ids:
            has_animal_farm_access = True

    if not (is_animal_owner or has_animal_farm_access):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this weighing record.")
    
    return db_weighing

@router.get("/", response_model=List[schemas.Weighing])
async def read_weighings(
    animal_id: Optional[uuid.UUID] = None, # Filtrar por animal
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtiene una lista de registros de pesajes, opcionalmente filtrados por animal.
    Solo muestra pesajes de animales que el usuario posee o a cuyas fincas tiene acceso.
    """
    # Lógica de autorización y filtrado delegada al CRUD para eficiencia
    # Asume un método crud_weighing.get_multi_by_user_and_filters_and_access
    weighings = await crud_weighing.get_multi_by_user_and_filters_and_access(
        db, 
        current_user_id=current_user.id,
        animal_id=animal_id,
        skip=skip, 
        limit=limit
    )
    return weighings

@router.put("/{weighing_id}", response_model=schemas.Weighing)
async def update_existing_weighing(
    weighing_id: uuid.UUID,
    weighing_update: schemas.WeighingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Actualiza los detalles de un registro de pesaje específico.
    Solo el propietario del animal asociado o quien tenga acceso a su finca puede actualizarlo.
    """
    db_weighing = await crud_weighing.get(db, id=weighing_id)
    if db_weighing is None:
        raise HTTPException(status_code=404, detail="Weighing record not found")
    
    is_animal_owner = db_weighing.animal.owner_user_id == current_user.id
    has_animal_farm_access = False
    if not is_animal_owner and db_weighing.animal.current_lot:
        user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
        user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
        all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

        if db_weighing.animal.current_lot.farm and db_weighing.animal.current_lot.farm.id in all_accessible_farm_ids:
            has_animal_farm_access = True

    if not (is_animal_owner or has_animal_farm_access):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this weighing record.")

    # Si se intenta cambiar el animal_id, validar el nuevo animal
    if weighing_update.animal_id and weighing_update.animal_id != db_weighing.animal_id:
        new_animal_db = await crud_animal.get(db, id=weighing_update.animal_id)
        if not new_animal_db:
            raise HTTPException(status_code=400, detail=f"New animal with ID '{weighing_update.animal_id}' not found.")
        
        # Validar acceso al nuevo animal
        is_new_animal_owner = new_animal_db.owner_user_id == current_user.id
        has_new_animal_farm_access = False
        if not is_new_animal_owner and new_animal_db.current_lot:
            user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
            user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
            all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

            if new_animal_db.current_lot.farm and new_animal_db.current_lot.farm.id in all_accessible_farm_ids:
                has_new_animal_farm_access = True
        
        if not (is_new_animal_owner or has_new_animal_farm_access):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to move weighing to new animal with ID '{weighing_update.animal_id}'.")

    try:
        updated_weighing = await crud_weighing.update(db, db_obj=db_weighing, obj_in=weighing_update) 
        if updated_weighing is None:
            raise HTTPException(status_code=500, detail="Failed to update weighing record unexpectedly.") 
        return updated_weighing
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{weighing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_weighing(
    weighing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Elimina un registro de pesaje específico.
    Solo el propietario del animal asociado o quien tenga acceso a su finca puede eliminarlo.
    """
    db_weighing = await crud_weighing.get(db, id=weighing_id)
    if db_weighing is None:
        raise HTTPException(status_code=404, detail="Weighing record not found")
    
    is_animal_owner = db_weighing.animal.owner_user_id == current_user.id
    has_animal_farm_access = False
    if not is_animal_owner and db_weighing.animal.current_lot:
        user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
        user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
        all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

        if db_weighing.animal.current_lot.farm and db_weighing.animal.current_lot.farm.id in all_accessible_farm_ids:
            has_animal_farm_access = True

    if not (is_animal_owner or has_animal_farm_access):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this weighing record.")
    
    deleted_weighing = await crud_weighing.remove(db, id=weighing_id)
    if not deleted_weighing:
        raise HTTPException(status_code=500, detail="Failed to delete weighing record unexpectedly.")
    return Response(status_code=status.HTTP_204_NO_CONTENT) # Retorno correcto para 204

