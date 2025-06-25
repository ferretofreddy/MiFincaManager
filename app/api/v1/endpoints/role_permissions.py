# app/api/v1/endpoints/role_permissions.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Any

from app import schemas, models
from app.crud import role_permission as crud_role_permission
from app.crud import role as crud_role
from app.crud import permission as crud_permission

from app.api import deps

get_db = deps.get_db
get_current_active_superuser = deps.get_current_active_superuser # Operaciones de permisos/roles suelen ser para superusuarios

router = APIRouter(
    prefix="/role_permissions",
    tags=["Role Permissions"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.RolePermission, status_code=status.HTTP_201_CREATED)
async def assign_permission_to_role(
    role_permission_in: schemas.RolePermissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) # Solo superusuarios pueden asignar permisos a roles
) -> Any:
    """
    Asigna un permiso a un rol.
    Requiere autenticación de superusuario.
    """
    # Validar que el rol y el permiso existan
    db_role = await crud_role.get(db, id=role_permission_in.role_id)
    if not db_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    
    db_permission = await crud_permission.get(db, id=role_permission_in.permission_id)
    if not db_permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found.")

    try:
        # El CRUD de RolePermission ya debería manejar la verificación de existencia
        role_permission = await crud_role_permission.create(db, obj_in=role_permission_in)
        return role_permission
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Association already exists or another error: {e}")

@router.get("/role/{role_id}/permissions", response_model=List[schemas.RolePermission])
async def get_permissions_for_role(
    role_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) # Superusuarios o usuarios con permisos específicos pueden ver esto
) -> List[schemas.RolePermission]:
    """
    Obtiene todos los permisos asignados a un rol específico.
    Requiere autenticación de superusuario (o permisos adecuados).
    """
    db_role = await crud_role.get(db, id=role_id)
    if not db_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    
    # Podrías añadir lógica de autorización más granular aquí si un usuario no-superadmin puede ver permisos de ciertos roles.
    
    return await crud_role_permission.get_permissions_for_role(db, role_id=role_id)

@router.delete("/role/{role_id}/permission/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_permission_from_role(
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser) # Solo superusuarios pueden remover permisos de roles
) -> Response:
    """
    Remueve un permiso de un rol.
    Requiere autenticación de superusuario.
    """
    # Validar que la asociación exista antes de intentar eliminar
    db_association = await crud_role_permission.get(db, role_id=role_id, permission_id=permission_id)
    if not db_association:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role-Permission association not found.")

    try:
        await crud_role_permission.remove(db, role_id=role_id, permission_id=permission_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error removing association: {e}")

