# app/api/v1/endpoints/user_farm_access.py
from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Response # Importa Response
from sqlalchemy.ext.asyncio import AsyncSession # Cambiado de Session a AsyncSession

from app import schemas, models
from app.crud import user as crud_user
from app.crud import farm as crud_farm
from app.crud import master_data as crud_master_data
from app.crud import user_farm_access as crud_user_farm_access # Importa la instancia CRUD


from app.api import deps # Módulo para dependencias como get_db y get_current_active_user

# Asumiendo que 'get_db' y 'get_current_active_user' etc. estarán en 'app/api/deps.py'
get_db = deps.get_db
get_current_active_user = deps.get_current_active_user
get_current_active_superuser = deps.get_current_active_superuser # Para superusuarios

router = APIRouter(
    prefix="/user_farm_access", # Añade un prefijo aquí también si no lo tienes en el __init__
    tags=["User Farm Access"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.UserFarmAccess, status_code=status.HTTP_201_CREATED)
async def create_user_farm_access(
    user_farm_access_in: schemas.UserFarmAccessCreate,
    db: AsyncSession = Depends(get_db), # Cambiado a AsyncSession
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Crea un nuevo registro de acceso de usuario a una granja.
    Requiere que el usuario autenticado tenga permisos para asignar accesos.
    Solo un superusuario O el propietario de la finca puede asignar acceso.
    """
    # 1. Validar que el usuario actual tiene permisos para asignar accesos
    farm_obj = await crud_farm.get(db, id=user_farm_access_in.farm_id) # Usar crud_farm
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

    # 2. Validar que el user_id existe
    user_obj = await crud_user.get(db, id=user_farm_access_in.user_id) # Usar crud_user
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_farm_access_in.user_id} not found."
        )

    # 3. Validar que el access_level_id es un tipo de MasterData válido para niveles de acceso
    access_level = await crud_master_data.get(db, id=user_farm_access_in.access_level_id) # Usar crud_master_data
    # Asumo que tienes un tipo de MasterData para "Nivel de Acceso", ej. category='access_level'
    if not access_level or access_level.category != "access_level": # Ajusta la categoría si es diferente
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Access Level with ID {user_farm_access_in.access_level_id} not found or invalid category in MasterData (must be 'access_level')."
        )

    # 4. Asegúrate de que el assigned_by_user_id sea el del usuario actual.
    if user_farm_access_in.assigned_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only assign access yourself (as the 'assigned_by_user')."
        )
    
    # 5. Verificar si ya existe este acceso para evitar duplicados
    existing_access = await crud_user_farm_access.get_by_user_and_farm(db, user_id=user_farm_access_in.user_id, farm_id=user_farm_access_in.farm_id)
    if existing_access:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has access to this farm."
        )

    user_farm_access_obj = await crud_user_farm_access.create(db, obj_in=user_farm_access_in) # Usar crud_user_farm_access
    return user_farm_access_obj

@router.get("/{access_id}", response_model=schemas.UserFarmAccess)
async def get_user_farm_access(
    access_id: UUID,
    db: AsyncSession = Depends(get_db), # Cambiado a AsyncSession
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Obtiene un registro de acceso de usuario a una granja por su ID.
    Accesible por superusuario, el usuario del acceso, el que lo asignó, o el propietario de la granja.
    """
    user_farm_access_obj = await crud_user_farm_access.get(db, id=access_id) # Usar crud_user_farm_access
    if not user_farm_access_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Farm Access not found."
        )
    
    # Lógica de autorización:
    is_authorized = False
    if current_user.is_superuser:
        is_authorized = True
    elif user_farm_access_obj.user_id == current_user.id: # El usuario del acceso puede verlo
        is_authorized = True
    elif user_farm_access_obj.assigned_by_user_id == current_user.id: # El que asignó el acceso puede verlo
        is_authorized = True
    elif user_farm_access_obj.farm.owner_user_id == current_user.id: # El propietario de la granja puede verlo
        is_authorized = True
    
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to retrieve this user farm access."
        )
    return user_farm_access_obj

@router.get("/", response_model=List[schemas.UserFarmAccess])
async def get_all_user_farm_accesses(
    db: AsyncSession = Depends(get_db), # Cambiado a AsyncSession
    current_user: models.User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None, # Filtro opcional por user_id
    farm_id: Optional[UUID] = None, # Filtro opcional por farm_id
) -> Any:
    """
    Obtiene registros de acceso de usuario a granja.
    Los superusuarios pueden ver todos; otros usuarios solo los propios o los de sus fincas.
    """
    if current_user.is_superuser:
        # Los superusuarios pueden filtrar por cualquier user_id o farm_id
        user_farm_accesses = await crud_user_farm_access.get_multi_with_filters(db, user_id=user_id, farm_id=farm_id, skip=skip, limit=limit) # Asume este método en crud
    else:
        # Los usuarios normales solo pueden ver sus propios accesos o los que asignaron, o los de sus fincas
        # Lógica más compleja, probablemente necesite un método CRUD que maneje la autorización
        # Por ejemplo, obtener accesos donde el current_user sea user_id, assigned_by_user_id, o owner de la farm_id
        
        # Obtener fincas propias del usuario
        user_owned_farms = await crud_farm.get_farms_by_owner(db, current_user.id)
        user_owned_farm_ids = [str(f.id) for f in user_owned_farms]

        # Obtener accesos asignados por el usuario
        user_assigned_accesses = await crud_user_farm_access.get_user_farm_accesses_by_assigned_user(db, current_user.id) # Asume este método

        # Obtener accesos donde el usuario es el user_id
        user_direct_accesses = await crud_user_farm_access.get_user_farm_accesses(db, current_user.id)

        # Unir todos los IDs de acceso que el usuario puede ver
        allowed_access_ids = set()
        for access in user_assigned_accesses:
            allowed_access_ids.add(str(access.id))
        for access in user_direct_accesses:
            allowed_access_ids.add(str(access.id))

        # Añadir accesos de fincas propias
        for farm_id_str in user_owned_farm_ids:
            farm_accesses = await crud_user_farm_access.get_farm_user_accesses(db, UUID(farm_id_str)) # Asume este método
            for access in farm_accesses:
                allowed_access_ids.add(str(access.id))
        
        # Obtener los objetos UserFarmAccess finales aplicando los filtros opcionales
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
    user_farm_access_update: schemas.UserFarmAccessUpdate, # Renombrado
    db: AsyncSession = Depends(get_db), # Cambiado a AsyncSession
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Actualiza un registro de acceso de usuario a una granja por su ID.
    Requiere que el usuario autenticado tenga permisos para modificar este acceso.
    """
    user_farm_access_obj = await crud_user_farm_access.get(db, id=access_id) # Usar crud_user_farm_access
    if not user_farm_access_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Farm Access not found."
        )
    
    # Lógica de autorización: solo el superusuario, el asignador original o el propietario de la granja.
    is_authorized = False
    if current_user.is_superuser:
        is_authorized = True
    elif user_farm_access_obj.assigned_by_user_id == current_user.id:
        is_authorized = True
    elif user_farm_access_obj.farm.owner_user_id == current_user.id: # Propietario de la granja puede actualizar accesos a su granja
        is_authorized = True
    
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this user farm access."
        )

    # Si se intenta cambiar el user_id o farm_id, no se permite una actualización directa.
    # Se debe crear un nuevo registro si la relación fundamental cambia.
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
    
    # Validar el nuevo access_level_id si se proporciona
    if user_farm_access_update.access_level_id and user_farm_access_update.access_level_id != user_farm_access_obj.access_level_id:
        access_level = await crud_master_data.get(db, id=user_farm_access_update.access_level_id)
        if not access_level or access_level.category != "access_level":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"New Access Level with ID {user_farm_access_update.access_level_id} not found or invalid category in MasterData."
            )

    updated_access = await crud_user_farm_access.update(db, db_obj=user_farm_access_obj, obj_in=user_farm_access_update) # Usar crud_user_farm_access
    return updated_access

@router.delete("/{access_id}", status_code=status.HTTP_204_NO_CONTENT) # Cambiado a 204 No Content
async def delete_user_farm_access(
    access_id: UUID,
    db: AsyncSession = Depends(get_db), # Cambiado a AsyncSession
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Elimina un registro de acceso de usuario a una granja por su ID.
    Requiere que el usuario autenticado tenga permisos para eliminar este acceso.
    """
    user_farm_access_obj = await crud_user_farm_access.get(db, id=access_id) # Usar crud_user_farm_access
    if not user_farm_access_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Farm Access not found."
        )
    
    # Lógica de autorización: solo el superusuario, el asignador original o el propietario de la granja.
    is_authorized = False
    if current_user.is_superuser:
        is_authorized = True
    elif user_farm_access_obj.assigned_by_user_id == current_user.id:
        is_authorized = True
    elif user_farm_access_obj.farm.owner_user_id == current_user.id: # Propietario de la granja puede eliminar accesos a su granja
        is_authorized = True
    
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this user farm access."
        )

    deleted_access = await crud_user_farm_access.remove(db, id=access_id) # Usar crud_user_farm_access
    if not deleted_access:
        raise HTTPException(status_code=404, detail="User Farm Access not found or could not be deleted")
    return Response(status_code=status.HTTP_204_NO_CONTENT) # Retorno correcto para 204

