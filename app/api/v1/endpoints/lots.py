# app/api/v1/endpoints/lots.py
from fastapi import APIRouter, Depends, HTTPException, status, Response # Importa Response
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Optional

# --- Importaciones de módulos centrales ---
from app import schemas, models
from app.crud import lot as crud_lot # Importa la instancia CRUD para lot
from app.crud import farm as crud_farm # Importa la instancia CRUD para farm
from app.crud import user_farm_access as crud_user_farm_access # Importa la instancia CRUD para user_farm_access


# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI

# Asumiendo que 'get_db' y 'get_current_user' estarán en 'app/api/deps.py'
get_db = deps.get_db
get_current_user = deps.get_current_user
get_current_active_user = deps.get_current_active_user
get_current_active_superuser = deps.get_current_active_superuser # Para superusuarios


router = APIRouter(
    prefix="/lots",
    tags=["Lots"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Lot, status_code=status.HTTP_201_CREATED)
async def create_new_lot(
    lot_in: schemas.LotCreate, # Renombrado para claridad
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Crea un nuevo lote en la finca.
    Requiere autenticación y el usuario debe ser propietario de la finca.
    """
    # 1. Verificar si la finca existe
    db_farm = await crud_farm.get(db, id=lot_in.farm_id) # Usar crud_farm.get
    if not db_farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found."
        )
    
    # 2. Verificar si el usuario es propietario de la finca
    if db_farm.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create lots in this farm."
        )
    
    # 3. Verificar si ya existe un lote con el mismo nombre en esta finca
    existing_lot_in_farm = await crud_lot.get_by_farm_id_and_name(db, farm_id=lot_in.farm_id, name=lot_in.name) # Usar crud_lot.get_by_farm_id_and_name
    if existing_lot_in_farm:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Lot with name '{lot_in.name}' already exists in this farm."
        )

    # 4. Crear el lote
    db_lot = await crud_lot.create(db=db, obj_in=lot_in) # Usar crud_lot.create
    return db_lot

@router.get("/{lot_id}", response_model=schemas.Lot)
async def read_lot(
    lot_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtiene un lote por su ID.
    Requiere autenticación y el usuario debe tener acceso a la finca del lote.
    """
    db_lot = await crud_lot.get(db, id=lot_id) # Usar crud_lot.get
    if not db_lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    
    # Verificar si el lote pertenece a una finca del usuario actual o si tiene acceso a ella
    is_owner_of_farm = db_lot.farm.owner_user_id == current_user.id
    has_farm_access = False
    if not is_owner_of_farm:
        # Verificar si tiene acceso compartido a la finca
        # Usar crud_user_farm_access.get_user_farm_accesses
        user_farm_accesses = await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)
        if any(access.farm_id == db_lot.farm.id for access in user_farm_accesses):
            has_farm_access = True
    
    if not (is_owner_of_farm or has_farm_access):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this lot."
        )
    
    return db_lot

@router.get("/", response_model=List[schemas.Lot])
async def read_lots(
    skip: int = 0, 
    limit: int = 100, 
    farm_id: Optional[uuid.UUID] = None, # Parámetro opcional para filtrar por finca
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtiene una lista de lotes.
    Si se proporciona farm_id, filtra por esa finca (y el usuario debe tener acceso).
    Si no se proporciona farm_id, devuelve todos los lotes de las fincas del usuario.
    """
    if farm_id:
        # Si se especifica una finca, verificar el acceso del usuario a esa finca
        db_farm = await crud_farm.get(db, id=farm_id) # Usar crud_farm.get
        if not db_farm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found.")
        
        is_owner_of_farm = db_farm.owner_user_id == current_user.id
        has_farm_access = False
        if not is_owner_of_farm:
            # Usar crud_user_farm_access.get_user_farm_accesses
            user_farm_accesses = await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)
            if any(access.farm_id == db_farm.id for access in user_farm_accesses):
                has_farm_access = True
        
        if not (is_owner_of_farm or has_farm_access):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access lots in this farm."
            )
        
        # Obtener lotes solo para esa finca
        lots = await crud_lot.get_multi_by_farm(db, farm_id=farm_id, skip=skip, limit=limit) # Usar crud_lot.get_multi_by_farm
    else:
        # Si no se especifica farm_id, obtener todos los lotes de las fincas del usuario actual
        user_farms = await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id) # Usar crud_farm.get_farms_by_owner
        user_farm_ids = [farm.id for farm in user_farms]

        # También incluir fincas donde el usuario tiene acceso compartido
        # Usar crud_user_farm_access.get_user_farm_accesses
        user_farm_accesses = await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)
        for access in user_farm_accesses:
            if access.farm_id not in user_farm_ids:
                user_farm_ids.append(access.farm_id)
        
        # Si tienes un método crud_lot.get_multi_by_farm_ids en tu CRUD de Lot, úsalo aquí.
        # Por ahora, mantendremos la iteración si no existe, pero es menos eficiente.
        all_lots_from_user_farms = []
        for fid in user_farm_ids:
            current_lots = await crud_lot.get_multi_by_farm(db, farm_id=fid, skip=0, limit=None) # Usar crud_lot.get_multi_by_farm
            all_lots_from_user_farms.extend(current_lots)
        
        # Aplicar paginación al resultado combinado
        lots = all_lots_from_user_farms[skip : skip + limit]

    return lots


@router.put("/{lot_id}", response_model=schemas.Lot)
async def update_existing_lot(
    lot_id: uuid.UUID,
    lot_update: schemas.LotUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Actualiza un lote existente por su ID.
    Requiere autenticación y el usuario debe ser propietario de la finca del lote.
    """
    db_lot = await crud_lot.get(db, id=lot_id) # Usar crud_lot.get
    if not db_lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    
    # Verificar si el lote pertenece a una finca del usuario actual
    if db_lot.farm.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this lot."
        )

    # Si se intenta cambiar el farm_id, verificar la nueva finca y si el usuario es propietario
    if lot_update.farm_id is not None and lot_update.farm_id != db_lot.farm_id:
        new_farm = await crud_farm.get(db, id=lot_update.farm_id) # Usar crud_farm.get
        if not new_farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="New farm for lot update not found."
            )
        if new_farm.owner_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to move lot to this new farm."
            )
    
    # Verificar unicidad del nombre si se actualiza el nombre
    if lot_update.name is not None and lot_update.name != db_lot.name:
        existing_lot_with_name = await crud_lot.get_by_farm_id_and_name(db, farm_id=db_lot.farm.id, name=lot_update.name) # Usar crud_lot.get_by_farm_id_and_name
        # Es importante que si el lot_update.farm_id es diferente, se verifique en la nueva finca.
        # Si se cambia el farm_id, la verificación de unicidad debe ser en el NUEVO farm_id.
        farm_id_for_check = lot_update.farm_id if lot_update.farm_id is not None else db_lot.farm.id
        existing_lot_with_name = await crud_lot.get_by_farm_id_and_name(db, farm_id=farm_id_for_check, name=lot_update.name)
        if existing_lot_with_name and existing_lot_with_name.id != lot_id: # Asegurarse de que no sea el mismo lote
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Lot with name '{lot_update.name}' already exists in this farm."
            )

    updated_lot = await crud_lot.update(db, db_obj=db_lot, obj_in=lot_update) # Usar crud_lot.update
    return updated_lot

@router.delete("/{lot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_lot(
    lot_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Elimina un lote por su ID.
    Requiere autenticación y el usuario debe ser propietario de la finca del lote.
    """
    db_lot = await crud_lot.get(db, id=lot_id) # Usar crud_lot.get
    if not db_lot:
        raise HTTPException(status_code=404, detail="Lot not found")

    # Verificar si el lote pertenece a una finca del usuario actual
    if db_lot.farm.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this lot."
        )

    deleted_lot = await crud_lot.remove(db, id=lot_id) # Usar crud_lot.remove
    if not deleted_lot:
        raise HTTPException(status_code=404, detail="Lot not found or could not be deleted")
    return Response(status_code=status.HTTP_204_NO_CONTENT) # Retorno correcto para 204

