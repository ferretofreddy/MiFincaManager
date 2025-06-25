# app/crud/module.py
from typing import Optional, List, Union, Dict, Any # Añadido Union, Dict, Any
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from sqlalchemy.exc import IntegrityError as DBIntegrityError # Importa la excepción de integridad de SQLAlchemy

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
        except DBIntegrityError as e: # Captura errores de integridad de la DB
            await db.rollback()
            raise AlreadyExistsError(f"Error de integridad al crear Module: {e}") from e
        except Exception as e:
            await db.rollback()
            if isinstance(e, AlreadyExistsError):
                raise e
            raise CRUDException(f"Error creating Module: {str(e)}") from e

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[Module]: # Cambiado module_id a id
        """
        Obtiene un módulo por su ID, cargando la relación con los permisos.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.permissions)
            )
            .filter(self.model.id == id) # Cambiado module_id a id
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

    async def update(self, db: AsyncSession, *, db_obj: Module, obj_in: Union[ModuleUpdate, Dict[str, Any]]) -> Module: # Añadido Union, Dict, Any
        """
        Actualiza un módulo existente.
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
                existing_module = await self.get_by_name(db, name=update_data["name"])
                if existing_module and existing_module.id != db_obj.id:
                    raise AlreadyExistsError(f"Module with name '{update_data['name']}' already exists.")

            updated_module = await super().update(db, db_obj=db_obj, obj_in=update_data)
            if updated_module:
                result = await db.execute(
                    select(self.model)
                    .options(
                        selectinload(self.model.permissions)
                    )
                    .filter(self.model.id == updated_module.id)
                )
                return result.scalars().first()
            return updated_module
        except Exception as e:
            await db.rollback()
            if isinstance(e, NotFoundError) or isinstance(e, AlreadyExistsError) or isinstance(e, CRUDException):
                raise e
            raise CRUDException(f"Error updating Module: {str(e)}") from e

    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[Module]: # Cambiado delete a remove
        """
        Elimina un módulo por su ID.
        """
        db_obj = await self.get(db, id)
        if not db_obj:
            raise NotFoundError(f"Module with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting Module: {str(e)}") from e

# Crea una instancia de CRUDModule que se puede importar y usar en los routers
module = CRUDModule(Module)
