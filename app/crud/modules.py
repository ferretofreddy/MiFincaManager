# app/crud/modules.py
from typing import Optional, List
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

# Importa el modelo Module y los esquemas de module
from app.models.module import Module
from app.schemas.module import ModuleCreate, ModuleUpdate

# Importa la CRUDBase y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException

class CRUDModule(CRUDBase[Module, ModuleCreate, ModuleUpdate]):
    """
    Clase CRUD específica para el modelo Module.
    Hereda la mayoría de las operaciones de CRUDBase.
    Implementa métodos específicos para Module.
    """

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Module]:
        """
        Obtiene un módulo por su nombre, cargando la relación con los permisos.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.permissions) # Carga la relación 'permissions'
            )
            .filter(self.model.name == name)
        )
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: ModuleCreate) -> Module:
        """
        Crea un nuevo módulo, verificando la unicidad del nombre.
        """
        # Verifica si ya existe un módulo con el mismo nombre
        existing_module = await self.get_by_name(db, name=obj_in.name)
        if existing_module:
            raise AlreadyExistsError(f"Module with name '{obj_in.name}' already exists.")

        try:
            db_obj = self.model(**obj_in.model_dump())
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj) # Obtiene el ID, created_at, updated_at
            
            # Recarga el módulo con sus relaciones para la respuesta
            result = await db.execute(
                select(Module)
                .options(
                    selectinload(Module.permissions)
                )
                .filter(Module.id == db_obj.id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating Module: {str(e)}") from e

    async def get(self, db: AsyncSession, module_id: uuid.UUID) -> Optional[Module]:
        """
        Obtiene un módulo por su ID, cargando la relación con los permisos.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.permissions)
            )
            .filter(self.model.id == module_id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Module]:
        """
        Obtiene una lista de módulos, cargando sus relaciones con los permisos.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.permissions)
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, db: AsyncSession, *, db_obj: Module, obj_in: ModuleUpdate) -> Module:
        """
        Actualiza un módulo existente.
        Después de la actualización, recarga el objeto con las relaciones necesarias.
        """
        updated_module = await super().update(db, db_obj=db_obj, obj_in=obj_in)
        if updated_module:
            result = await db.execute(
                select(self.model)
                .options(
                    selectinload(self.model.permissions)
                )
                .filter(self.model.id == updated_module.id)
            )
            return result.scalar_one_or_none()
        return updated_module

# Crea una instancia de CRUDModule que se puede importar y usar en los routers
module = CRUDModule(Module)
