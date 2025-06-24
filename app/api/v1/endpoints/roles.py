# routers/roles.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List

# --- Importaciones de módulos centrales ---
from app import crud, schemas, models # Acceso de alto nivel a tus módulos principales

# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI (get_db, get_current_user, etc.)

router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Role, status_code=status.HTTP_201_CREATED)
async def create_new_role(
    role: schemas.RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Solo usuarios autenticados
):
    """
    Crea un nuevo rol.
    NOTA: En un entorno de producción, esta operación debería estar restringida
    solo a usuarios con permisos de administrador. Aquí se asume que cualquier
    usuario autenticado puede acceder para fines de desarrollo inicial.
    """
    db_role = await crud.get_role_by_name(db, name=role.name)
    if db_role:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Role with this name already exists"
        )
    return await crud.create_role(db=db, role=role)

@router.get("/{role_id}", response_model=schemas.Role)
async def read_role(
    role_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Solo usuarios autenticados
):
    """
    Obtiene un rol por su ID.
    """
    db_role = await crud.get_role(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.get("/", response_model=List[schemas.Role])
async def read_roles(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Solo usuarios autenticados
):
    """
    Obtiene una lista de roles.
    """
    roles = await crud.get_roles(db, skip=skip, limit=limit)
    return roles

@router.put("/{role_id}", response_model=schemas.Role)
async def update_existing_role(
    role_id: uuid.UUID,
    role_update: schemas.RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Solo usuarios autenticados
):
    """
    Actualiza un rol existente por su ID.
    NOTA: En un entorno de producción, esta operación debería estar restringida
    solo a usuarios con permisos de administrador.
    """
    db_role = await crud.get_role(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Opcional: Verificar si el nuevo nombre ya existe si se está actualizando el nombre
    if role_update.name and role_update.name != db_role.name:
        existing_role_with_name = await crud.get_role_by_name(db, name=role_update.name)
        if existing_role_with_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Role with this name already exists."
            )

    updated_role = await crud.update_role(db, role_id=role_id, role_update=role_update)
    return updated_role

@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_role(
    role_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Solo usuarios autenticados
):
    """
    Elimina un rol por su ID.
    NOTA: En un entorno de producción, esta operación debería estar restringida
    solo a usuarios con permisos de administrador.
    """
    success = await crud.delete_role(db, role_id=role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found")
    return {"message": "Role deleted successfully"}

