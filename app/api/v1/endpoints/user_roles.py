# app/api/v1/endpoints/user_roles.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Any

from app import schemas, models
from app.crud import user_role as crud_user_role
from app.crud import user as crud_user
from app.crud import role as crud_role
from app.crud.exceptions import AlreadyExistsError, NotFoundError, CRUDException # Importar excepciones CRUD

from app.api import deps

get_db = deps.get_db
get_current_active_superuser = deps.get_current_active_superuser 
get_current_active_user = deps.get_current_active_user 

router = APIRouter(
    prefix="/user_roles",
    tags=["User Roles"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.UserRole, status_code=status.HTTP_201_CREATED)
async def assign_role_to_user(
    user_role_in: schemas.UserRoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) 
) -> Any:
    """
    Asigna un rol a un usuario.
    Requiere autenticación de superusuario.
    """
    # Validar que el usuario y el rol existan
    db_user = await crud_user.get(db, id=user_role_in.user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    db_role = await crud_role.get(db, id=user_role_in.role_id)
    if not db_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    
    # Asegurar que el assigned_by_user_id sea el del usuario actual si no se provee,
    # o validar que el usuario actual tenga permiso para asignar en nombre de otro
    # (por simplicidad, asumimos que current_user.id es quien asigna)
    user_role_in.assigned_by_user_id = current_user.id # Sobrescribir para asegurar consistencia

    try:
        user_role = await crud_user_role.create(db, obj_in=user_role_in)
        return user_role
    except AlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except NotFoundError as e: 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except CRUDException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Error al asignar rol: {str(e)}"
        )
    except Exception as e:
        # Para cualquier otro error inesperado, devuelve un 500
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")


@router.get("/user/{user_id}/roles", response_model=List[schemas.UserRole])
async def get_roles_for_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user) 
) -> List[schemas.UserRole]:
    """
    Obtiene todos los roles asignados a un usuario específico.
    Un usuario normal solo puede ver sus propios roles; superusuarios pueden ver cualquier rol.
    """
    if str(user_id) != str(current_user.id) and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view roles for this user."
        )
    
    db_user = await crud_user.get(db, id=user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return await crud_user_role.get_roles_for_user(db, user_id=user_id)

@router.delete("/user/{user_id}/role/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role_from_user(
    user_id: uuid.UUID,
    role_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) 
) -> Response:
    """
    Remueve un rol de un usuario.
    Requiere autenticación de superusuario.
    """
    db_association = await crud_user_role.get(db, user_id=user_id, role_id=role_id)
    if not db_association:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User-Role association not found.")

    try:
        await crud_user_role.remove_role_from_user(db, user_id=user_id, role_id=role_id) # Usar el nombre de método correcto
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error removing association: {e}")

