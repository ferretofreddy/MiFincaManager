# app/crud/permission.py
from typing import Optional, List, Union, Dict, Any # Añadido Union, Dict, Any
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_ # Importa 'and_' para combinaciones de filtros
from sqlalchemy.exc import IntegrityError as DBIntegrityError # Importa la excepción de integridad de SQLAlchemy

# Importa el modelo Permission y los esquemas de permission
from app.models.permission import Permission
from app.models.module import Module # Importado para validación
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
            # Validar module_id si se proporciona
            if obj_in.module_id:
                module_exists_q = await db.execute(select(Module).filter(Module.id == obj_in.module_id))
                if not module_exists_q.scalar_one_or_none():
                    raise NotFoundError(f"Module with ID {obj_in.module_id} not found.")

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
            return result.scalars().first()
        except DBIntegrityError as e:
            await db.rollback()
            raise AlreadyExistsError(f"Error de integridad al crear Permission: {e}") from e
        except Exception as e:
            await db.rollback()
            if isinstance(e, (NotFoundError, AlreadyExistsError)):
                raise e
            raise CRUDException(f"Error creating Permission: {str(e)}") from e

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[Permission]: # Cambiado permission_id a id
        """
        Obtiene un permiso por su ID, cargando la relación con el módulo y los roles.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.module),
                selectinload(self.model.roles)
            )
            .filter(self.model.id == id) # Cambiado permission_id a id
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

    async def update(self, db: AsyncSession, *, db_obj: Permission, obj_in: Union[PermissionUpdate, Dict[str, Any]]) -> Permission: # Añadido Union, Dict, Any
        """
        Actualiza un permiso existente.
        Después de la actualización, recarga el objeto con las relaciones necesarias.
        """
        try:
            # Si obj_in es un Pydantic model, conviértelo a dict y excluye unset
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)

            # Si el nombre se está actualizando, verifica unicidad
            if "name" in update_data and update_data["name"] != db_obj.name:
                existing_permission = await self.get_by_name(db, name=update_data["name"])
                if existing_permission and existing_permission.id != db_obj.id:
                    raise AlreadyExistsError(f"Permission with name '{update_data['name']}' already exists.")
            
            # Si se intenta cambiar el module_id, valida que el nuevo módulo exista
            if "module_id" in update_data and update_data["module_id"] != db_obj.module_id:
                module_exists_q = await db.execute(select(Module).filter(Module.id == update_data["module_id"]))
                if not module_exists_q.scalar_one_or_none():
                    raise NotFoundError(f"Module with ID {update_data['module_id']} not found.")

            updated_permission = await super().update(db, db_obj=db_obj, obj_in=update_data)
            if updated_permission:
                result = await db.execute(
                    select(self.model)
                    .options(
                        selectinload(self.model.module),
                        selectinload(self.model.roles)
                    )
                    .filter(self.model.id == updated_permission.id)
                )
                return result.scalars().first()
            return updated_permission
        except Exception as e:
            await db.rollback()
            if isinstance(e, (NotFoundError, AlreadyExistsError, CRUDException)):
                raise e
            raise CRUDException(f"Error updating Permission: {str(e)}") from e

    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[Permission]: # Cambiado delete a remove
        """
        Elimina un permiso por su ID.
        """
        db_obj = await self.get(db, id)
        if not db_obj:
            raise NotFoundError(f"Permission with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting Permission: {str(e)}") from e

# Crea una instancia de CRUDPermission que se puede importar y usar en los routers
permission = CRUDPermission(Permission)
