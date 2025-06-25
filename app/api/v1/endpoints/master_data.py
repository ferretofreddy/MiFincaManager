# app/api/v1/endpoints/master_data.py
from fastapi import APIRouter, Depends, HTTPException, status, Response # Importa Response
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Optional

# --- Importaciones de módulos centrales ---
from app import schemas, models
from app.crud import master_data as crud_master_data # Importa la instancia CRUD para master_data


# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI

# Asumiendo que 'get_db' y 'get_current_active_user' etc. estarán en 'app/api/deps.py'
get_db = deps.get_db
get_current_active_user = deps.get_current_active_user
get_current_active_superuser = deps.get_current_active_superuser # Para superusuarios


router = APIRouter(
    prefix="/master-data",
    tags=["Master Data"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.MasterData, status_code=status.HTTP_201_CREATED)
async def create_new_master_data_item(
    item_in: schemas.MasterDataCreate, # Renombrado
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) # Solo superusuarios pueden crear MasterData por defecto
):
    """
    Crea un nuevo dato maestro.
    Requiere autenticación de superusuario.
    Verifica que no exista otro dato maestro con la misma categoría y nombre.
    """
    # Verificar si ya existe un item con la misma categoría y nombre
    existing_item = await crud_master_data.get_by_category_and_name(db, category=item_in.category, name=item_in.name) # Usar crud_master_data
    if existing_item:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Master data item with category '{item_in.category}' and name '{item_in.name}' already exists."
        )
    
    db_item = await crud_master_data.create(db=db, obj_in=item_in, created_by_user_id=current_user.id) # Usar crud_master_data
    return db_item

@router.get("/{master_data_id}", response_model=schemas.MasterData)
async def read_master_data_item(
    master_data_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user) # Cualquier usuario activo puede leer MasterData
):
    """
    Obtiene un dato maestro por su ID.
    """
    db_item = await crud_master_data.get(db, id=master_data_id) # Usar crud_master_data
    if db_item is None:
        raise HTTPException(status_code=404, detail="Master data item not found")
    
    return db_item

@router.get("/", response_model=List[schemas.MasterData])
async def read_master_data_items(
    skip: int = 0, 
    limit: int = 100, 
    category: Optional[str] = None, # Parámetro opcional para filtrar por categoría
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user) # Cualquier usuario activo puede leer MasterData
):
    """
    Obtiene una lista de datos maestros, opcionalmente filtrada por categoría.
    """
    if category:
        items = await crud_master_data.get_by_category(db, category=category, skip=skip, limit=limit) # Usar crud_master_data
    else:
        items = await crud_master_data.get_all(db, skip=skip, limit=limit) # Usar crud_master_data
    return items

@router.put("/{master_data_id}", response_model=schemas.MasterData)
async def update_existing_master_data_item(
    master_data_id: uuid.UUID,
    item_update: schemas.MasterDataUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) # Solo superusuarios pueden actualizar MasterData
):
    """
    Actualiza un dato maestro existente por su ID.
    Requiere autenticación de superusuario.
    """
    db_item = await crud_master_data.get(db, id=master_data_id) # Usar crud_master_data
    if db_item is None:
        raise HTTPException(status_code=404, detail="Master data item not found")
    
    # Si se intenta cambiar category o name, verificar unicidad
    if (item_update.category is not None and item_update.category != db_item.category) or \
       (item_update.name is not None and item_update.name != db_item.name):
        
        target_category = item_update.category if item_update.category is not None else db_item.category
        target_name = item_update.name if item_update.name is not None else db_item.name

        existing_item_with_new_props = await crud_master_data.get_by_category_and_name(db, category=target_category, name=target_name) # Usar crud_master_data
        
        # Si ya existe un item con la nueva combinación de categoría y nombre, y no es el mismo item que estamos actualizando
        if existing_item_with_new_props and existing_item_with_new_props.id != master_data_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Master data item with category '{target_category}' and name '{target_name}' already exists."
            )

    updated_item = await crud_master_data.update(db, db_obj=db_item, obj_in=item_update) # Usar crud_master_data
    return updated_item

@router.delete("/{master_data_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_master_data_item(
    master_data_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) # Solo superusuarios pueden eliminar MasterData
):
    """
    Elimina un dato maestro por su ID.
    Requiere autenticación de superusuario.
    """
    db_item = await crud_master_data.get(db, id=master_data_id) # Usar crud_master_data
    if db_item is None:
        raise HTTPException(status_code=404, detail="Master data item not found")
    
    deleted_item = await crud_master_data.remove(db, id=master_data_id) # Usar crud_master_data
    if not deleted_item:
        raise HTTPException(status_code=404, detail="Master data item not found or could not be deleted")
    return Response(status_code=status.HTTP_204_NO_CONTENT) # Retorno correcto para 204

