# app/crud/role_permissions.py 
from typing import Optional, List
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import delete

# Importa el modelo RolePermission y los esquemas
from app.models.role_permission import RolePermission
from app.schemas.role_permission import RolePermissionCreate
# No usaremos CRUDBase aquí ya que las operaciones son muy específicas.
# from app.crud.base import CRUDBase 
from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException

class CRUDRolePermission:
    """
    Clase CRUD específica para la asociación RolePermission.
    Gestiona la asignación y revocación de permisos a roles.
    """
    def __init__(self, model):
        self.model = model

    async def get(self, db: AsyncSession, role_id: uuid.UUID, permission_id: uuid.UUID) -> Optional[RolePermission]:
        """
        Obtiene una asociación RolePermission específica por IDs de rol y permiso,
        cargando los objetos Role y Permission asociados.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.role),
                selectinload(self.model.permission)
            )
            .filter(self.model.role_id == role_id, self.model.permission_id == permission_id)
        )
        return result.scalar_one_or_none()

    async def assign_permission_to_role(self, db: AsyncSession, role_id: uuid.UUID, permission_id: uuid.UUID) -> RolePermission:
        """
        Asigna un permiso a un rol.
        Verifica si la asociación ya existe antes de crearla.
        """
        existing_association = await self.get(db, role_id, permission_id)
        if existing_association:
            raise AlreadyExistsError(f"Permission {permission_id} is already assigned to role {role_id}.")

        try:
            # Crea una instancia del modelo RolePermission
            db_obj = self.model(role_id=role_id, permission_id=permission_id)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj) # Recarga para obtener assigned_at

            # Opcional: recargar con relaciones si la respuesta necesita más detalles
            reloaded_obj = await self.get(db, role_id, permission_id)
            return reloaded_obj if reloaded_obj else db_obj

        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error assigning permission {permission_id} to role {role_id}: {str(e)}") from e

    async def remove_permission_from_role(self, db: AsyncSession, role_id: uuid.UUID, permission_id: uuid.UUID):
        """
        Remueve un permiso de un rol.
        """
        db_obj = await self.get(db, role_id, permission_id)
        if not db_obj:
            raise NotFoundError(f"Permission {permission_id} is not assigned to role {role_id}.")

        try:
            await db.execute(
                delete(self.model).where(
                    self.model.role_id == role_id,
                    self.model.permission_id == permission_id
                )
            )
            await db.commit()
            return {"message": "Association removed successfully."}
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error removing permission {permission_id} from role {role_id}: {str(e)}") from e
    
    async def get_permissions_for_role(self, db: AsyncSession, role_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[RolePermission]:
        """
        Obtiene todas las asociaciones de permisos para un rol específico,
        cargando los objetos Permission asociados.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.permission), # Carga el objeto Permission asociado
                selectinload(self.model.role) # Carga el objeto Role asociado (opcional, ya lo sabes)
            )
            .filter(self.model.role_id == role_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

# Crea una instancia de CRUDRolePermission que se puede importar y usar en los routers
role_permission = CRUDRolePermission(RolePermission)
