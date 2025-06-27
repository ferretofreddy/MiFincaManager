# app/api/v1/endpoints/user_farm_access.py
from typing import Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Response # Importa Response
from sqlalchemy.ext.asyncio import AsyncSession 

from app import schemas, models
from app.crud import user as crud_user
from app.crud import farm as crud_farm
from app.crud import master_data as crud_master_data
from app.crud import user_farm_access as crud_user_farm_access 


from app.api import deps 

get_db = deps.get_db
get_current_active_user = deps.get_current_active_user
get_current_active_superuser = deps.get_current_active_superuser 

router = APIRouter(
    prefix="/user_farm_access", 
    tags=["User Farm Access"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.UserFarmAccess, status_code=status.HTTP_201_CREATED)
async def create_user_farm_access(
    user_farm_access_in: schemas.UserFarmAccessCreate,
    db: AsyncSession = Depends(get_db), 
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Crea un nuevo registro de acceso de usuario a una granja.
    Requiere que el usuario autenticado tenga permisos para asignar accesos.
    Solo un superusuario O el propietario de la finca puede asignar acceso.
    """
    farm_obj = await crud_farm.get(db, id=user_farm_access_in.farm_id) 
    if not farm_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm with ID {user_farm_access_in.farm_id} not found."
        )

    if not (current_user.is_superuser or farm_obj.owner_user_id == current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create user farm access for this farm (only superuser or farm owner)."
        )

    user_obj = await crud_user.get(db, id=user_farm_access_in.user_id) 
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_farm_access_in.user_id} not found."
        )

    access_level = await crud_master_data.get(db, id=user_farm_access_in.access_level_id) 
    if not access_level or access_level.category != "access_level": 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Access Level with ID {user_farm_access_in.access_level_id} not found or invalid category in MasterData (must be 'access_level')."
        )

    if user_farm_access_in.assigned_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only assign access yourself (as the 'assigned_by_user')."
        )
    
    existing_access = await crud_user_farm_access.get_by_user_and_farm(db, user_id=user_farm_access_in.user_id, farm_id=user_farm_access_in.farm_id)
    if existing_access:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has access to this farm."
        )

    user_farm_access_obj = await crud_user_farm_access.create(db, obj_in=user_farm_access_in) 
    return user_farm_access_obj

@router.get("/{access_id}", response_model=schemas.UserFarmAccess)
async def get_user_farm_access(
    access_id: UUID,
    db: AsyncSession = Depends(get_db), 
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Obtiene un registro de acceso de usuario a una granja por su ID.
    Accesible por superusuario, el usuario del acceso, el que lo asignó, o el propietario de la granja.
    """
    user_farm_access_obj = await crud_user_farm_access.get(db, id=access_id) 
    if not user_farm_access_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Farm Access not found."
        )
    
    is_authorized = False
    if current_user.is_superuser:
        is_authorized = True
    elif user_farm_access_obj.user_id == current_user.id: 
        is_authorized = True
    elif user_farm_access_obj.assigned_by_user_id == current_user.id: 
        is_authorized = True
    elif user_farm_access_obj.farm.owner_user_id == current_user.id: 
        is_authorized = True
    
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to retrieve this user farm access."
        )
    return user_farm_access_obj

@router.get("/", response_model=List[schemas.UserFarmAccess])
async def get_all_user_farm_accesses(
    db: AsyncSession = Depends(get_db), 
    current_user: models.User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None, 
    farm_id: Optional[UUID] = None, 
) -> Any:
    """
    Obtiene registros de acceso de usuario a granja.
    Los superusuarios pueden ver todos; otros usuarios solo los propios o los de sus fincas.
    """
    if current_user.is_superuser:
        user_farm_accesses = await crud_user_farm_access.get_multi_with_filters(db, user_id=user_id, farm_id=farm_id, skip=skip, limit=limit) 
    else:
        user_owned_farms = await crud_farm.get_farms_by_owner(db, current_user.id)
        user_owned_farm_ids = [str(f.id) for f in user_owned_farms]

        user_assigned_accesses = await crud_user_farm_access.get_user_farm_accesses_by_assigned_user(db, current_user.id) 

        user_direct_accesses = await crud_user_farm_access.get_user_farm_accesses(db, current_user.id)

        allowed_access_ids = set()
        for access in user_assigned_accesses:
            allowed_access_ids.add(str(access.id))
        for access in user_direct_accesses:
            allowed_access_ids.add(str(access.id))

        for farm_id_str in user_owned_farm_ids:
            farm_accesses = await crud_user_farm_access.get_farm_user_accesses(db, UUID(farm_id_str)) 
            for access in farm_accesses:
                allowed_access_ids.add(str(access.id))
        
        all_relevant_accesses = []
        for access_id_str in allowed_access_ids:
            access_obj = await crud_user_farm_access.get(db, UUID(access_id_str))
            if access_obj:
                add_to_list = True
                if user_id and access_obj.user_id != user_id:
                    add_to_list = False
                if farm_id and access_obj.farm_id != farm_id:
                    add_to_list = False
                if add_to_list:
                    all_relevant_accesses.append(access_obj)
        
        user_farm_accesses = all_relevant_accesses[skip : skip + limit]

    return user_farm_accesses

@router.put("/{access_id}", response_model=schemas.UserFarmAccess)
async def update_user_farm_access(
    access_id: UUID,
    user_farm_access_update: schemas.UserFarmAccessUpdate, 
    db: AsyncSession = Depends(get_db), 
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Actualiza un registro de acceso de usuario a una granja por su ID.
    Requiere que el usuario autenticado tenga permisos para modificar este acceso.
    """
    user_farm_access_obj = await crud_user_farm_access.get(db, id=access_id) 
    if not user_farm_access_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Farm Access not found."
        )
    
    is_authorized = False
    if current_user.is_superuser:
        is_authorized = True
    elif user_farm_access_obj.assigned_by_user_id == current_user.id:
        is_authorized = True
    elif user_farm_access_obj.farm.owner_user_id == current_user.id: 
        is_authorized = True
    
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this user farm access."
        )

    if user_farm_access_update.user_id and user_farm_access_update.user_id != user_farm_access_obj.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Changing the 'user_id' for an existing access record is not allowed. Delete and create a new one."
        )
    if user_farm_access_update.farm_id and user_farm_access_update.farm_id != user_farm_access_obj.farm_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Changing the 'farm_id' for an existing access record is not allowed. Delete and create a new one."
        )
    
    if user_farm_access_update.access_level_id and user_farm_access_update.access_level_id != user_farm_access_obj.access_level_id:
        access_level = await crud_master_data.get(db, id=user_farm_access_update.access_level_id)
        if not access_level or access_level.category != "access_level":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"New Access Level with ID {user_farm_access_update.access_level_id} not found or invalid category in MasterData."
            )

    updated_access = await crud_user_farm_access.update(db, db_obj=user_farm_access_obj, obj_in=user_farm_access_update) 
    return updated_access

@router.delete(
    "/{access_id}",
    status_code=status.HTTP_204_NO_CONTENT, # Este es el código que no debe tener cuerpo
    # response_model=None, # Puedes añadir esto explícitamente si quieres, pero no es estrictamente necesario
    summary="Elimina un registro de acceso de usuario a una granja",
    description="Elimina un registro de acceso existente por su ID. Requiere autenticación de superusuario."
)
async def delete_user_farm_access(
    access_id: UUID,
    db: AsyncSession = Depends(get_db), 
    current_user: models.User = Depends(get_current_active_superuser), # Superusuario para eliminar
):
    """
    Elimina un registro de acceso de usuario a una granja por su ID.
    Args:
        access_id (uuid.UUID): El ID del registro de acceso a eliminar.
        db (AsyncSession): La sesión de base de datos.
        current_user (models.User): El superusuario autenticado que realiza la operación.
    Raises:
        HTTPException: Si el registro no se encuentra o si ocurre un error durante la eliminación.
    """
    try:
        # Aquí es donde se elimina el registro.
        # crud.user_farm_access.remove(db, id=access_id) ya lanza NotFoundError si no existe
        deleted_access = await crud.user_farm_access.remove(db, id=access_id)
        
        # === ¡CORRECCIÓN CLAVE AQUÍ! ===
        # Si la eliminación fue exitosa, no se retorna nada para un 204.
        # FastAPI maneja el 204 automáticamente si la función no retorna nada.
        # El "if not deleted_access" y el "return Response(...)" son redundantes
        # y causaban el error de "body for 204".
        return # Simplemente retornar sin valor para un 204 NO CONTENT
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except CRUDException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al eliminar acceso de usuario a granja: {e}"
        )

