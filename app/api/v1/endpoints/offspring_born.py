# app/api/v1/endpoints/offspring_born.py

from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas, crud, models
from app.api import deps # Acceso a las dependencias de FastAPI (get_db, get_current_user, etc.)
from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException

# Se inicializa el router de API para los endpoints de OffspringBorn
router = APIRouter()

@router.post(
    "/",
    response_model=schemas.OffspringBorn, # El esquema de respuesta para la creación
    status_code=status.HTTP_201_CREATED,
    summary="Crea un nuevo evento de nacimiento de descendencia",
    description="Permite registrar un nuevo evento de nacimiento, asociándolo con los padres y la nueva descendencia. Requiere autenticación de usuario activo."
)
async def create_offspring_born(
    offspring_born_in: schemas.OffspringBornCreate, # El esquema para la creación
    db: AsyncSession = Depends(deps.get_db), # Dependencia para obtener la sesión de DB
    current_user: models.User = Depends(deps.get_current_active_user) # Dependencia para asegurar un usuario activo
) -> schemas.OffspringBorn:
    """
    Crea un nuevo evento de nacimiento de descendencia.

    Args:
        offspring_born_in (schemas.OffspringBornCreate): Los datos para crear el evento de nacimiento.
        db (AsyncSession): La sesión de base de datos.
        current_user (models.User): El usuario autenticado que realiza la operación.

    Returns:
        schemas.OffspringBorn: El evento de nacimiento creado con sus detalles.

    Raises:
        HTTPException: Si ocurre un error durante la creación (ej. IDs no encontrados, error de base de datos).
    """
    try:
        # Asigna el ID del usuario que registra el evento
        offspring_born_in.recorded_by_user_id = current_user.id
        
        # Llama a la función CRUD para crear el evento de nacimiento
        offspring_born_event = await crud.offspring_born.create(db, obj_in=offspring_born_in)
        return offspring_born_event
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except AlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )
    except CRUDException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al crear evento de nacimiento: {e}"
        )


@router.get(
    "/",
    response_model=List[schemas.OffspringBorn], # El esquema de respuesta para una lista de eventos
    summary="Obtiene todos los eventos de nacimiento de descendencia",
    description="Recupera una lista de todos los eventos de nacimiento registrados. Requiere autenticación de usuario activo."
)
async def read_offspring_born_events(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0, # Parámetro opcional para paginación (offset)
    limit: int = 100, # Parámetro opcional para paginación (límite)
    current_user: models.User = Depends(deps.get_current_active_user) # Dependencia para asegurar un usuario activo
) -> List[schemas.OffspringBorn]:
    """
    Recupera una lista de todos los eventos de nacimiento de descendencia.

    Args:
        db (AsyncSession): La sesión de base de datos.
        skip (int): El número de registros a omitir para paginación.
        limit (int): El número máximo de registros a devolver.
        current_user (models.User): El usuario autenticado que realiza la operación.

    Returns:
        List[schemas.OffspringBorn]: Una lista de eventos de nacimiento.

    Raises:
        HTTPException: Si ocurre un error de base de datos.
    """
    try:
        offspring_born_events = await crud.offspring_born.get_multi(db, skip=skip, limit=limit)
        return offspring_born_events
    except CRUDException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al obtener eventos de nacimiento: {e}"
        )


@router.get(
    "/{offspring_born_id}",
    response_model=schemas.OffspringBorn, # El esquema de respuesta para un solo evento
    summary="Obtiene un evento de nacimiento de descendencia por ID",
    description="Recupera los detalles de un evento de nacimiento específico usando su ID. Requiere autenticación de usuario activo."
)
async def read_offspring_born_by_id(
    offspring_born_id: uuid.UUID, # El ID del evento de nacimiento a recuperar
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user) # Dependencia para asegurar un usuario activo
) -> schemas.OffspringBorn:
    """
    Recupera un evento de nacimiento de descendencia por su ID.

    Args:
        offspring_born_id (uuid.UUID): El ID del evento de nacimiento.
        db (AsyncSession): La sesión de base de datos.
        current_user (models.User): El usuario autenticado que realiza la operación.

    Returns:
        schemas.OffspringBorn: El evento de nacimiento encontrado.

    Raises:
        HTTPException: Si el evento no se encuentra o si ocurre un error de base de datos.
    """
    try:
        offspring_born_event = await crud.offspring_born.get(db, id=offspring_born_id)
        if not offspring_born_event:
            raise NotFoundError(f"Evento de nacimiento con ID {offspring_born_id} no encontrado.")
        return offspring_born_event
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except CRUDException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al obtener evento de nacimiento: {e}"
        )


@router.put(
    "/{offspring_born_id}",
    response_model=schemas.OffspringBorn, # El esquema de respuesta para la actualización
    summary="Actualiza un evento de nacimiento de descendencia",
    description="Actualiza los detalles de un evento de nacimiento existente. Requiere autenticación de usuario activo."
)
async def update_offspring_born(
    offspring_born_id: uuid.UUID, # El ID del evento de nacimiento a actualizar
    offspring_born_in: schemas.OffspringBornUpdate, # Los datos para la actualización
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user) # Dependencia para asegurar un usuario activo
) -> schemas.OffspringBorn:
    """
    Actualiza un evento de nacimiento de descendencia existente.

    Args:
        offspring_born_id (uuid.UUID): El ID del evento de nacimiento a actualizar.
        offspring_born_in (schemas.OffspringBornUpdate): Los datos actualizados del evento.
        db (AsyncSession): La sesión de base de datos.
        current_user (models.User): El usuario autenticado que realiza la operación.

    Returns:
        schemas.OffspringBorn: El evento de nacimiento actualizado.

    Raises:
        HTTPException: Si el evento no se encuentra o si ocurre un error durante la actualización.
    """
    try:
        # Se obtiene el evento existente para asegurar que existe antes de intentar actualizar
        existing_offspring_born = await crud.offspring_born.get(db, id=offspring_born_id)
        if not existing_offspring_born:
            raise NotFoundError(f"Evento de nacimiento con ID {offspring_born_id} no encontrado.")
        
        # Llama a la función CRUD para actualizar
        updated_offspring_born = await crud.offspring_born.update(db, db_obj=existing_offspring_born, obj_in=offspring_born_in)
        return updated_offspring_born
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except AlreadyExistsError as e: # Aunque menos común en update por ID, puede ocurrir con campos únicos
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )
    except CRUDException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al actualizar evento de nacimiento: {e}"
        )


@router.delete(
    "/{offspring_born_id}",
    status_code=status.HTTP_204_NO_CONTENT, # No hay contenido de respuesta para eliminación exitosa
    summary="Elimina un evento de nacimiento de descendencia",
    description="Elimina un evento de nacimiento existente por su ID. Requiere autenticación de superusuario."
)
async def delete_offspring_born(
    offspring_born_id: uuid.UUID, # El ID del evento de nacimiento a eliminar
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser) # Dependencia para asegurar un superusuario
):
    """
    Elimina un evento de nacimiento de descendencia por su ID.

    Args:
        offspring_born_id (uuid.UUID): El ID del evento de nacimiento a eliminar.
        db (AsyncSession): La sesión de base de datos.
        current_user (models.User): El superusuario autenticado que realiza la operación.

    Raises:
        HTTPException: Si el evento no se encuentra o si ocurre un error durante la eliminación.
    """
    try:
        await crud.offspring_born.remove(db, id=offspring_born_id)
        # FastAPI automáticamente maneja el 204 No Content
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except CRUDException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al eliminar evento de nacimiento: {e}"
        )
