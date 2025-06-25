# app/crud/role.py
from typing import Optional, List
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

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
        Obtiene un rol por su nombre, cargando las relaciones con permisos y usuarios.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.permissions), # Carga la relación 'permissions'
                selectinload(self.model.users) # Carga la relación 'users'
            )
            .filter(self.model.name == name)
        )
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: RoleCreate) -> Role:
        """
        Crea un nuevo rol, verificando la unicidad del nombre.
        """
        # Verifica si ya existe un rol con el mismo nombre
        existing_role = await self.get_by_name(db, name=obj_in.name)
        if existing_role:
            raise AlreadyExistsError(f"Role with name '{obj_in.name}' already exists.")

        try:
            db_obj = self.model(**obj_in.model_dump())
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj) # Obtiene el ID, created_at, updated_at
            
            # Recarga el rol con sus relaciones para la respuesta
            result = await db.execute(
                select(Role)
                .options(
                    selectinload(Role.permissions),
                    selectinload(Role.users)
                )
                .filter(Role.id == db_obj.id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating Role: {str(e)}") from e

    async def get(self, db: AsyncSession, role_id: uuid.UUID) -> Optional[Role]:
        """
        Obtiene un rol por su ID, cargando las relaciones con permisos y usuarios.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.permissions),
                selectinload(self.model.users)
            )
            .filter(self.model.id == role_id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Role]:
        """
        Obtiene una lista de roles, cargando sus relaciones con permisos y usuarios.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.permissions),
                selectinload(self.model.users)
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


    async def update(self, db: AsyncSession, *, db_obj: Role, obj_in: RoleUpdate) -> Role:
        """
        Actualiza un rol existente.
        Después de la actualización, recarga el objeto con las relaciones necesarias.
        """
        updated_role = await super().update(db, db_obj=db_obj, obj_in=obj_in)
        if updated_role:
            result = await db.execute(
                select(self.model)
                .options(
                    selectinload(self.model.permissions),
                    selectinload(self.model.users)
                )
                .filter(self.model.id == updated_role.id)
            )
            # Cambiado a scalars().first()
            return result.scalars().first()
        return updated_role

# Crea una instancia de CRUDRole que se puede importar y usar en los routers
role = CRUDRole(Role)
