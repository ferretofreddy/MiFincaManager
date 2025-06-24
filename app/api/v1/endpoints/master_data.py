# routers/master_data.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Optional

# --- Importaciones de módulos centrales ---
from app import crud, schemas, models # Acceso de alto nivel a tus módulos principales

# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI (get_db, get_current_user, etc.)

router = APIRouter(
    prefix="/master-data",
    tags=["Master Data"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.MasterData, status_code=status.HTTP_201_CREATED)
async def create_new_master_data_item(
    item: schemas.MasterDataCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Crea un nuevo dato maestro.
    Requiere autenticación.
    Verifica que no exista otro dato maestro con la misma categoría y nombre.
    """
    # Verificar si ya existe un item con la misma categoría y nombre
    # CORRECCIÓN AQUÍ: Cambiado 'get_master_data_by_category_name' a 'get_master_data_by_category_and_name'
    existing_item = await crud.get_master_data_by_category_and_name(db, item.category, item.name)
    if existing_item:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Master data item with category '{item.category}' and name '{item.name}' already exists."
        )
    
    db_item = await crud.create_master_data(db=db, master_data=item, created_by_user_id=current_user.id)
    return db_item

@router.get("/{master_data_id}", response_model=schemas.MasterData)
async def read_master_data_item(
    master_data_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Requiere autenticación
):
    """
    Obtiene un dato maestro por su ID.
    """
    db_item = await crud.get_master_data(db, master_data_id=master_data_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Master data item not found")
    
    # Opcional: Podrías añadir lógica de autorización si solo ciertos usuarios pueden ver ciertos tipos de master data.
    # Por ahora, se asume que cualquier usuario autenticado puede ver cualquier master data.
    return db_item

@router.get("/", response_model=List[schemas.MasterData])
async def read_master_data_items(
    skip: int = 0, 
    limit: int = 100, 
    category: Optional[str] = None, # Parámetro opcional para filtrar por categoría
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Requiere autenticación
):
    """
    Obtiene una lista de datos maestros, opcionalmente filtrada por categoría.
    """
    if category:
        items = await crud.get_master_data_by_category(db, category=category, skip=skip, limit=limit)
    else:
        items = await crud.get_all_master_data(db, skip=skip, limit=limit)
    return items

@router.put("/{master_data_id}", response_model=schemas.MasterData)
async def update_existing_master_data_item(
    master_data_id: uuid.UUID,
    item_update: schemas.MasterDataUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Requiere autenticación
):
    """
    Actualiza un dato maestro existente por su ID.
    Solo el usuario que lo creó (o un admin) puede actualizarlo.
    """
    db_item = await crud.get_master_data(db, master_data_id=master_data_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Master data item not found")
    
    # Verificar que el usuario actual sea quien lo creó
    if db_item.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this master data item."
        )

    # Si se intenta cambiar category o name, verificar unicidad
    if (item_update.category is not None and item_update.category != db_item.category) or \
       (item_update.name is not None and item_update.name != db_item.name):
        
        target_category = item_update.category if item_update.category is not None else db_item.category
        target_name = item_update.name if item_update.name is not None else db_item.name

        existing_item_with_new_props = await crud.get_master_data_by_category_and_name(db, target_category, target_name)
        
        # Si ya existe un item con la nueva combinación de categoría y nombre, y no es el mismo item que estamos actualizando
        if existing_item_with_new_props and existing_item_with_new_props.id != master_data_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Master data item with category '{target_category}' and name '{target_name}' already exists."
            )

    updated_item = await crud.update_master_data(db, master_data_id=master_data_id, master_data_update=item_update)
    return updated_item

@router.delete("/{master_data_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_master_data_item(
    master_data_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Requiere autenticación
):
    """
    Elimina un dato maestro por su ID.
    Solo el usuario que lo creó (o un admin) puede eliminarlo.
    """
    db_item = await crud.get_master_data(db, master_data_id=master_data_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Master data item not found")
    
    # Verificar que el usuario actual sea quien lo creó
    if db_item.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this master data item."
        )
    
    success = await crud.delete_master_data(db, master_data_id=master_data_id)
    if not success:
        raise HTTPException(status_code=404, detail="Master data item not found or could not be deleted")
    return {"message": "Master data item deleted successfully"}

