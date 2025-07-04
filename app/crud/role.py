# app/crud/role.py
from typing import Optional, List, Union, Dict, Any 
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError as DBIntegrityError 

# Importa el modelo Role y los esquemas de role
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate

# Importa la CRUDBase y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException

class CRUDRole(CRUDBase[Role, RoleCreate, RoleUpdate]):
    """
    Clase CRUD específica para el modelo Role.
    Hereda la mayoría de las operaciones de CRUDBase.
    Implementa métodos específicos para Role.
    """

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Role]:
        """
        Obtiene un rol por su nombre, cargando las relaciones con permisos, usuarios y asociaciones.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.permissions), 
                selectinload(self.model.users_with_this_role),
                selectinload(self.model.role_permissions_associations), # Añadido
                selectinload(self.model.user_roles_associations) # Añadido
            )
            .filter(self.model.name == name)
        )
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: RoleCreate) -> Role:
        """
        Crea un nuevo rol, verificando la unicidad del nombre.
        """
        existing_role = await self.get_by_name(db, name=obj_in.name) # get_by_name ahora carga todo
        if existing_role:
            raise AlreadyExistsError(f"Role with name '{obj_in.name}' already exists.")

        try:
            db_obj = self.model(**obj_in.model_dump())
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj) 
            
            # Recarga el objeto para asegurar que todas las relaciones estén cargadas para la respuesta
            result = await db.execute(
                select(Role)
                .options(
                    selectinload(Role.permissions),
                    selectinload(Role.users_with_this_role),
                    selectinload(Role.role_permissions_associations), # Añadido
                    selectinload(Role.user_roles_associations) # Añadido
                )
                .filter(Role.id == db_obj.id)
            )
            return result.scalars().first()
        except DBIntegrityError as e:
            await db.rollback()
            raise AlreadyExistsError(f"Error de integridad al crear Role: {e}") from e
        except Exception as e:
            await db.rollback()
            if isinstance(e, AlreadyExistsError):
                raise e
            raise CRUDException(f"Error creating Role: {str(e)}") from e

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[Role]: 
        """
        Obtiene un rol por su ID, cargando las relaciones con permisos, usuarios y asociaciones.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.permissions),
                selectinload(self.model.users_with_this_role),
                selectinload(self.model.role_permissions_associations), # Añadido
                selectinload(self.model.user_roles_associations) # Añadido
            )
            .filter(self.model.id == id) 
        )
        return result.scalar_one_or_none()
    
    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Role]:
        """
        Obtiene una lista de roles, cargando todas las relaciones necesarias para serialización.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.permissions),
                selectinload(self.model.users_with_this_role),
                selectinload(self.model.role_permissions_associations),  # ¡Añade esto!
                selectinload(self.model.user_roles_associations) # Añadido
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


    async def update(self, db: AsyncSession, *, db_obj: Role, obj_in: Union[RoleUpdate, Dict[str, Any]]) -> Role: 
        """
        Actualiza un rol existente.
        Después de la actualización, recarga el objeto con las relaciones necesarias.
        """
        try:
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)

            if "name" in update_data and update_data["name"] != db_obj.name:
                existing_role_with_name = await self.get_by_name(db, name=update_data["name"]) # get_by_name ahora carga todo
                if existing_role_with_name and existing_role_with_name.id != db_obj.id:
                    raise AlreadyExistsError(f"Role with name '{update_data['name']}' already exists.")

            updated_role = await super().update(db, db_obj=db_obj, obj_in=update_data)
            if updated_role:
                # Recarga el objeto para asegurar que todas las relaciones estén cargadas para la respuesta
                result = await db.execute(
                    select(self.model)
                    .options(
                        selectinload(self.model.permissions),
                        selectinload(self.model.users_with_this_role),
                        selectinload(self.model.role_permissions_associations), # Añadido
                        selectinload(self.model.user_roles_associations) # Añadido
                    )
                    .filter(self.model.id == updated_role.id)
                )
                return result.scalars().first()
            return updated_role
        except Exception as e:
            await db.rollback()
            if isinstance(e, (NotFoundError, AlreadyExistsError, CRUDException)):
                raise e
            raise CRUDException(f"Error updating Role: {str(e)}") from e

    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[Role]: 
        """
        Elimina un rol por su ID.
        """
        db_obj = await self.get(db, id) # get ahora carga todo
        if not db_obj:
            raise NotFoundError(f"Role with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting Role: {str(e)}") from e

role = CRUDRole(Role)
