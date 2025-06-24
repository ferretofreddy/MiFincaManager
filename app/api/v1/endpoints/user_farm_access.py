# app/api/endpoints/user_farm_access.py
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps # Módulo para dependencias como get_db y get_current_active_user

router = APIRouter()

@router.post("/", response_model=schemas.UserFarmAccess, status_code=status.HTTP_201_CREATED)
def create_user_farm_access(
    user_farm_access_in: schemas.UserFarmAccessCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user), # Requiere autenticación
) -> Any:
    """
    Crea un nuevo registro de acceso de usuario a una granja.
    Requiere que el usuario autenticado tenga permisos para asignar accesos.
    """
    # Aquí puedes añadir lógica de validación de permisos si es necesario.
    # Por ejemplo, solo un superusuario o un administrador de la granja puede asignar accesos.
    # if not current_user.is_superuser:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Not enough permissions to create user farm access."
    #     )

    # Validar que el user_id y farm_id existen
    user_obj = crud.user.get(db, id=user_farm_access_in.user_id)
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_farm_access_in.user_id} not found."
        )

    farm_obj = crud.farm.get(db, id=user_farm_access_in.farm_id)
    if not farm_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm with ID {user_farm_access_in.farm_id} not found."
        )

    # Validar que el access_level_id es un tipo de MasterData válido para niveles de acceso
    access_level = crud.master_data.get(db, id=user_farm_access_in.access_level_id)
    # Asumo que tienes un tipo de MasterData para "Nivel de Acceso".
    # Puedes añadir una validación más estricta aquí para asegurar que el access_level.type sea el correcto.
    if not access_level:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Access Level with ID {user_farm_access_in.access_level_id} not found in MasterData."
        )

    # Asegúrate de que el assigned_by_user_id sea el del usuario actual.
    if user_farm_access_in.assigned_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only assign access yourself."
        )

    user_farm_access_obj = crud.user_farm_access.create(db, obj_in=user_farm_access_in)
    return user_farm_access_obj

@router.get("/{access_id}", response_model=schemas.UserFarmAccess)
def get_user_farm_access(
    access_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Obtiene un registro de acceso de usuario a una granja por su ID.
    """
    user_farm_access_obj = crud.user_farm_access.get(db, id=access_id)
    if not user_farm_access_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Farm Access not found."
        )
    # Opcional: Validar que el usuario actual tenga acceso a ver este registro
    # Por ejemplo, que sea el usuario del acceso, el usuario que lo asignó,
    # un administrador de la granja, o un superusuario.
    # if not (current_user.is_superuser or \
    #         user_farm_access_obj.user_id == current_user.id or \
    #         user_farm_access_obj.farm.owner_id == current_user.id): # Esto último asume una relación.
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Not enough permissions to retrieve this user farm access."
    #     )
    return user_farm_access_obj

@router.get("/", response_model=List[schemas.UserFarmAccess])
def get_all_user_farm_accesses(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Obtiene todos los registros de acceso de usuario a granja.
    Solo accesible por superusuarios o administradores con permisos adecuados.
    """
    if not current_user.is_superuser:
        # Si no es superusuario, solo puede ver sus propios accesos o los que él asignó.
        # Esto es una simplificación, la lógica de permisos real podría ser más compleja.
        return crud.user_farm_access.get_user_farm_accesses(db, user_id=current_user.id) # Ejemplo
        # O también: crud.user_farm_access.get_multi(db, owner_id=current_user.id, skip=skip, limit=limit)
    
    # Para superusuarios, obtiene todos
    user_farm_accesses = crud.user_farm_access.get_multi(db, skip=skip, limit=limit)
    return user_farm_accesses

@router.put("/{access_id}", response_model=schemas.UserFarmAccess)
def update_user_farm_access(
    access_id: UUID,
    user_farm_access_in: schemas.UserFarmAccessUpdate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Actualiza un registro de acceso de usuario a una granja por su ID.
    Requiere que el usuario autenticado tenga permisos para modificar este acceso.
    """
    user_farm_access_obj = crud.user_farm_access.get(db, id=access_id)
    if not user_farm_access_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Farm Access not found."
        )
    # Lógica de autorización: solo el superusuario, el asignador original o el propietario de la granja.
    # if not (current_user.is_superuser or \
    #         user_farm_access_obj.assigned_by_user_id == current_user.id or \
    #         user_farm_access_obj.farm.owner_id == current_user.id):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Not enough permissions to update this user farm access."
    #     )

    # Si se intenta cambiar el user_id o farm_id, podría ser necesario un nuevo registro en lugar de una actualización.
    if user_farm_access_in.user_id and user_farm_access_in.user_id != user_farm_access_obj.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Changing the 'user_id' for an existing access record is not allowed. Create a new one."
        )
    if user_farm_access_in.farm_id and user_farm_access_in.farm_id != user_farm_access_obj.farm_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Changing the 'farm_id' for an existing access record is not allowed. Create a new one."
        )

    user_farm_access_obj = crud.user_farm_access.update(db, db_obj=user_farm_access_obj, obj_in=user_farm_access_in)
    return user_farm_access_obj

@router.delete("/{access_id}", response_model=schemas.UserFarmAccess)
def delete_user_farm_access(
    access_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Elimina un registro de acceso de usuario a una granja por su ID.
    Requiere que el usuario autenticado tenga permisos para eliminar este acceso.
    """
    user_farm_access_obj = crud.user_farm_access.get(db, id=access_id)
    if not user_farm_access_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Farm Access not found."
        )
    # Lógica de autorización: solo el superusuario o el asignador original.
    # if not (current_user.is_superuser or \
    #         user_farm_access_obj.assigned_by_user_id == current_user.id):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Not enough permissions to delete this user farm access."
    #     )

    user_farm_access_obj = crud.user_farm_access.remove(db, id=access_id)
    return user_farm_access_obj
