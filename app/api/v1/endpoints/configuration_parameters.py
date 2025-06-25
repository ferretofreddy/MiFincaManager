# app/api/v1/endpoints/configuration_parameters.py
from fastapi import APIRouter, Depends, HTTPException, status, Response # Importa Response
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List

# --- Importaciones de módulos centrales ---
from app import schemas, models
from app.crud import configuration_parameter as crud_configuration_parameter # Importa la instancia CRUD para configuration_parameter


# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI

# Asumiendo que 'get_db' y 'get_current_active_user' etc. estarán en 'app/api/deps.py'
get_db = deps.get_db
get_current_active_user = deps.get_current_active_user
get_current_active_superuser = deps.get_current_active_superuser # Para superusuarios


router = APIRouter(
    prefix="/config-parameters",
    tags=["Configuration Parameters"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.ConfigurationParameter, status_code=status.HTTP_201_CREATED)
async def create_new_configuration_parameter(
    config_param_in: schemas.ConfigurationParameterCreate, # Renombrado
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) # Solo superusuarios pueden crear parámetros
):
    """
    Crea un nuevo parámetro de configuración.
    Requiere autenticación de superusuario.
    """
    db_config_param = await crud_configuration_parameter.get_by_name(db, name=config_param_in.name) # Usar crud_configuration_parameter
    if db_config_param:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Configuration parameter with this name already exists"
        )
    
    # Si tu esquema de creación tiene 'created_by_user_id', pásalo.
    # Asumiendo que el modelo y CRUD lo manejan.
    return await crud_configuration_parameter.create(
        db=db, 
        obj_in=config_param_in, 
        created_by_user_id=current_user.id # Pasa el created_by_user_id
    )

@router.get("/{config_param_id}", response_model=schemas.ConfigurationParameter)
async def read_configuration_parameter(
    config_param_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user) # Cualquier usuario activo puede leer parámetros
):
    """
    Obtiene un parámetro de configuración por su ID.
    """
    db_config_param = await crud_configuration_parameter.get(db, id=config_param_id) # Usar crud_configuration_parameter
    if db_config_param is None:
        raise HTTPException(status_code=404, detail="Configuration parameter not found")
    return db_config_param

@router.get("/by-name/{name}", response_model=schemas.ConfigurationParameter) # Cambiado parameter_name a name
async def read_configuration_parameter_by_name(
    name: str, # Cambiado parameter_name a name
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user) # Cualquier usuario activo puede leer parámetros
):
    """
    Obtiene un parámetro de configuración por su nombre.
    """
    db_config_param = await crud_configuration_parameter.get_by_name(db, name=name) # Usar crud_configuration_parameter
    if db_config_param is None:
        raise HTTPException(status_code=404, detail="Configuration parameter not found")
    return db_config_param

@router.get("/", response_model=List[schemas.ConfigurationParameter])
async def read_all_configuration_parameters(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user) # Cualquier usuario activo puede leer parámetros
):
    """
    Obtiene una lista de todos los parámetros de configuración.
    """
    config_params = await crud_configuration_parameter.get_multi(db, skip=skip, limit=limit) # Usar crud_configuration_parameter
    return config_params

@router.put("/{config_param_id}", response_model=schemas.ConfigurationParameter)
async def update_existing_configuration_parameter(
    config_param_id: uuid.UUID,
    config_param_update: schemas.ConfigurationParameterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) # Solo superusuarios pueden actualizar parámetros
):
    """
    Actualiza un parámetro de configuración existente por su ID.
    Requiere autenticación de superusuario.
    """
    db_config_param = await crud_configuration_parameter.get(db, id=config_param_id) # Usar crud_configuration_parameter
    if db_config_param is None:
        raise HTTPException(status_code=404, detail="Configuration parameter not found")
    
    # Si se intenta cambiar el nombre, verificar que el nuevo nombre no exista
    if config_param_update.name and config_param_update.name != db_config_param.name: # Cambiado parameter_name a name
        existing_param_with_name = await crud_configuration_parameter.get_by_name(db, name=config_param_update.name) # Usar crud_configuration_parameter
        if existing_param_with_name and existing_param_with_name.id != config_param_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Configuration parameter with this name already exists."
            )

    updated_config_param = await crud_configuration_parameter.update(
        db, 
        db_obj=db_config_param, 
        obj_in=config_param_update,
        # Si tu CRUD requiere last_updated_by_user_id en el update, pásalo:
        # last_updated_by_user_id=current_user.id 
    )
    return updated_config_param

@router.delete("/{config_param_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_configuration_parameter(
    config_param_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) # Solo superusuarios pueden eliminar parámetros
):
    """
    Elimina un parámetro de configuración por su ID.
    Requiere autenticación de superusuario.
    """
    db_config_param = await crud_configuration_parameter.get(db, id=config_param_id)
    if not db_config_param: # Verificar que exista antes de intentar eliminarlo
        raise HTTPException(status_code=404, detail="Configuration parameter not found")

    deleted_param = await crud_configuration_parameter.remove(db, id=config_param_id) # Usar crud_configuration_parameter
    if not deleted_param:
        raise HTTPException(status_code=404, detail="Configuration parameter not found or could not be deleted")
    return Response(status_code=status.HTTP_204_NO_CONTENT) # Retorno correcto para 204

