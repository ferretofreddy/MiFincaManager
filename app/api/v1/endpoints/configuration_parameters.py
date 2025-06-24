# routers/configuration_parameters.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List

# --- Importaciones de módulos centrales ---
from app import crud, schemas, models # Acceso de alto nivel a tus módulos principales

# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI (get_db, get_current_user, etc.)

router = APIRouter(
    prefix="/config-parameters",
    tags=["Configuration Parameters"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.ConfigurationParameter, status_code=status.HTTP_201_CREATED)
async def create_new_configuration_parameter(
    config_param: schemas.ConfigurationParameterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Solo usuarios autenticados
):
    """
    Crea un nuevo parámetro de configuración.
    NOTA: En un entorno de producción, esta operación debería estar restringida
    solo a usuarios con permisos de administrador.
    """
    db_config_param = await crud.get_configuration_parameter_by_name(db, parameter_name=config_param.parameter_name)
    if db_config_param:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Configuration parameter with this name already exists"
        )
    return await crud.create_configuration_parameter(
        db=db, 
        config_param=config_param, 
        last_updated_by_user_id=current_user.id
    )

@router.get("/{config_param_id}", response_model=schemas.ConfigurationParameter)
async def read_configuration_parameter(
    config_param_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Solo usuarios autenticados
):
    """
    Obtiene un parámetro de configuración por su ID.
    """
    db_config_param = await crud.get_configuration_parameter(db, config_param_id=config_param_id)
    if db_config_param is None:
        raise HTTPException(status_code=404, detail="Configuration parameter not found")
    return db_config_param

@router.get("/by-name/{parameter_name}", response_model=schemas.ConfigurationParameter)
async def read_configuration_parameter_by_name(
    parameter_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Solo usuarios autenticados
):
    """
    Obtiene un parámetro de configuración por su nombre.
    """
    db_config_param = await crud.get_configuration_parameter_by_name(db, parameter_name=parameter_name)
    if db_config_param is None:
        raise HTTPException(status_code=404, detail="Configuration parameter not found")
    return db_config_param

@router.get("/", response_model=List[schemas.ConfigurationParameter])
async def read_all_configuration_parameters(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Solo usuarios autenticados
):
    """
    Obtiene una lista de todos los parámetros de configuración.
    """
    config_params = await crud.get_all_configuration_parameters(db, skip=skip, limit=limit)
    return config_params

@router.put("/{config_param_id}", response_model=schemas.ConfigurationParameter)
async def update_existing_configuration_parameter(
    config_param_id: uuid.UUID,
    config_param_update: schemas.ConfigurationParameterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Solo usuarios autenticados
):
    """
    Actualiza un parámetro de configuración existente por su ID.
    NOTA: En un entorno de producción, esta operación debería estar restringida
    solo a usuarios con permisos de administrador.
    """
    db_config_param = await crud.get_configuration_parameter(db, config_param_id=config_param_id)
    if db_config_param is None:
        raise HTTPException(status_code=404, detail="Configuration parameter not found")
    
    # Si se intenta cambiar el nombre, verificar que el nuevo nombre no exista
    if config_param_update.parameter_name and config_param_update.parameter_name != db_config_param.parameter_name:
        existing_param_with_name = await crud.get_configuration_parameter_by_name(db, parameter_name=config_param_update.parameter_name)
        if existing_param_with_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Configuration parameter with this name already exists."
            )

    updated_config_param = await crud.update_configuration_parameter(
        db, 
        config_param_id=config_param_id, 
        config_param_update=config_param_update,
        last_updated_by_user_id=current_user.id
    )
    return updated_config_param

@router.delete("/{config_param_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_configuration_parameter(
    config_param_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Solo usuarios autenticados
):
    """
    Elimina un parámetro de configuración por su ID.
    NOTA: En un entorno de producción, esta operación debería estar restringida
    solo a usuarios con permisos de administrador.
    """
    success = await crud.delete_configuration_parameter(db, config_param_id=config_param_id)
    if not success:
        raise HTTPException(status_code=404, detail="Configuration parameter not found")
    return {"message": "Configuration parameter deleted successfully"}

