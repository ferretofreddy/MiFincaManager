# app/crud/permission.py
from typing import Optional, List
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_ # Importa 'and_' para combinaciones de filtros

# Importa el modelo Permission y los esquemas de permission
from app.models.permission import Permission
from app.schemas.permission import PermissionCreate, PermissionUpdate

# Importa la CRUDBase y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException

class CRUDPermission(CRUDBase[Permission, PermissionCreate, PermissionUpdate]):
    """
    Clase CRUD específica para el modelo Permission.
    Hereda la mayoría de las operaciones de CRUDBase.
    Implementa métodos específicos para Permission.
    """

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Permission]:
        """
        Obtiene un permiso por su nombre, cargando la relación con el módulo y los roles.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.module), # Carga la relación 'module'
                selectinload(self.model.roles) # Carga la relación 'roles'
            )
            .filter(self.model.name == name)
        )
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: PermissionCreate) -> Permission:
        """
        Crea un nuevo permiso, verificando la unicidad del nombre.
        """
        # Verifica si ya existe un permiso con el mismo nombre
        existing_permission = await self.get_by_name(db, name=obj_in.name)
        if existing_permission:
            raise AlreadyExistsError(f"Permission with name '{obj_in.name}' already exists.")

        try:
            db_obj = self.model(**obj_in.model_dump())
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj) # Obtiene el ID, created_at, updated_at
            
            # Recarga el permiso con sus relaciones para la respuesta
            result = await db.execute(
                select(Permission)
                .options(
                    selectinload(Permission.module),
                    selectinload(Permission.roles)
                )
                .filter(Permission.id == db_obj.id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating Permission: {str(e)}") from e

    async def get(self, db: AsyncSession, permission_id: uuid.UUID) -> Optional[Permission]:
        """
        Obtiene un permiso por su ID, cargando la relación con el módulo y los roles.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.module),
                selectinload(self.model.roles)
            )
            .filter(self.model.id == permission_id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Permission]:
        """
        Obtiene una lista de permisos, cargando sus relaciones con el módulo y los roles.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.module),
                selectinload(self.model.roles)
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_multi_by_module(self, db: AsyncSession, module_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Permission]:
        """
        Obtiene una lista de permisos filtrada por ID de módulo.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.module),
                selectinload(self.model.roles)
            )
            .filter(self.model.module_id == module_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, db: AsyncSession, *, db_obj: Permission, obj_in: PermissionUpdate) -> Permission:
        """
        Actualiza un permiso existente.
        Después de la actualización, recarga el objeto con las relaciones necesarias.
        """
        updated_permission = await super().update(db, db_obj=db_obj, obj_in=obj_in)
        if updated_permission:
            result = await db.execute(
                select(self.model)
                .options(
                    selectinload(self.model.module),
                    selectinload(self.model.roles)
                )
                .filter(self.model.id == updated_permission.id)
            )
            # Cambiado a scalars().first()
            return result.scalars().first()
        return updated_permission

# Crea una instancia de CRUDPermission que se puede importar y usar en los routers
permission = CRUDPermission(Permission)
