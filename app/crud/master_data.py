# app/crud/master_data.py
from typing import Optional, List, Dict, Any, Union # Añadido Union
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_ # Importa 'and_' para combinaciones de filtros
from sqlalchemy.exc import IntegrityError as DBIntegrityError # Importa la excepción de integridad de SQLAlchemy

# Importa el modelo MasterData y los esquemas de master_data
from app.models.master_data import MasterData
from app.schemas.master_data import MasterDataCreate, MasterDataUpdate

# Importa la CRUDBase y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException

class CRUDMasterData(CRUDBase[MasterData, MasterDataCreate, MasterDataUpdate]):
    """
    Clase CRUD específica para el modelo MasterData.
    Hereda la mayoría de las operaciones de CRUDBase.
    Implementa métodos específicos para MasterData.
    """

    async def create(self, db: AsyncSession, *, obj_in: MasterDataCreate, created_by_user_id: uuid.UUID) -> MasterData:
        """
        Crea un nuevo dato maestro.
        created_by_user_id es un parámetro adicional.
        Verifica la unicidad del nombre dentro de la misma categoría.
        """
        # Verifica si ya existe un dato maestro con el mismo nombre y categoría
        existing_master_data_q = await db.execute(
            select(MasterData).filter(
                and_(MasterData.category == obj_in.category, MasterData.name == obj_in.name)
            )
        )
        if existing_master_data_q.scalar_one_or_none():
            raise AlreadyExistsError(f"MasterData with name '{obj_in.name}' in category '{obj_in.category}' already exists.")

        try:
            db_obj = self.model(**obj_in.model_dump(), created_by_user_id=created_by_user_id)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj) # Obtiene el ID, created_at, updated_at
            
            # Recarga el dato maestro con la relación created_by_user para la respuesta
            result = await db.execute(
                select(MasterData)
                .options(selectinload(MasterData.created_by_user))
                .filter(MasterData.id == db_obj.id)
            )
            return result.scalar_one_or_none()
        except DBIntegrityError as e: # Captura errores de integridad de la DB
            await db.rollback()
            raise AlreadyExistsError(f"Error de integridad al crear MasterData: {e}") from e
        except Exception as e:
            await db.rollback()
            if isinstance(e, AlreadyExistsError): # Re-lanza AlreadyExistsError si ya la manejaste
                raise e
            raise CRUDException(f"Error creating MasterData: {str(e)}") from e

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[MasterData]: # Cambiado master_data_id a id
        """
        Obtiene un dato maestro por su ID, cargando la relación con el usuario creador.
        """
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.created_by_user))
            .filter(self.model.id == id) # Cambiado master_data_id a id
        )
        return result.scalar_one_or_none()
    
    async def get_by_category_and_name(self, db: AsyncSession, category: str, name: str) -> Optional[MasterData]:
        """
        Obtiene un dato maestro por su categoría y nombre.
        """
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.created_by_user))
            .filter(and_(self.model.category == category, self.model.name == name))
        )
        return result.scalar_one_or_none()

    async def get_multi_by_category(self, db: AsyncSession, category: str, skip: int = 0, limit: int = 100) -> List[MasterData]:
        """
        Obtiene una lista de datos maestros filtrada por categoría.
        """
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.created_by_user))
            .filter(self.model.category == category)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[MasterData]:
        """
        Obtiene todos los datos maestros, cargando la relación con el usuario creador.
        """
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.created_by_user))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, db: AsyncSession, *, db_obj: MasterData, obj_in: Union[MasterDataUpdate, Dict[str, Any]]) -> MasterData: # Añadido Union, Dict, Any
        """
        Actualiza un dato maestro existente.
        Después de la actualización, recarga el objeto con las relaciones necesarias.
        """
        try:
            # Si obj_in es un Pydantic model, conviértelo a dict y excluye unset
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)

            # Si la categoría o el nombre se están actualizando, verifica unicidad
            category_changed = "category" in update_data and update_data["category"] != db_obj.category
            name_changed = "name" in update_data and update_data["name"] != db_obj.name

            if category_changed or name_changed:
                target_category = update_data.get("category", db_obj.category)
                target_name = update_data.get("name", db_obj.name)
                
                existing_item_q = await db.execute(
                    select(MasterData).filter(and_(
                        MasterData.category == target_category,
                        MasterData.name == target_name,
                        MasterData.id != db_obj.id # Excluir el propio objeto
                    ))
                )
                if existing_item_q.scalar_one_or_none():
                    raise AlreadyExistsError(f"MasterData with category '{target_category}' and name '{target_name}' already exists.")

            updated_master_data = await super().update(db, db_obj=db_obj, obj_in=update_data)
            if updated_master_data:
                result = await db.execute(
                    select(self.model)
                    .options(selectinload(self.model.created_by_user))
                    .filter(self.model.id == updated_master_data.id)
                )
                return result.scalars().first()
            return updated_master_data
        except Exception as e:
            await db.rollback()
            if isinstance(e, (NotFoundError, AlreadyExistsError, CRUDException)):
                raise e
            raise CRUDException(f"Error updating MasterData record: {str(e)}") from e

    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[MasterData]: # Cambiado delete a remove
        """
        Elimina un registro de dato maestro por su ID.
        """
        db_obj = await self.get(db, id) # Primero obtenemos el objeto para asegurar que existe y para devolverlo
        if not db_obj:
            raise NotFoundError(f"MasterData record with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj # Retorna el objeto eliminado
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting MasterData record: {str(e)}") from e

# Crea una instancia de CRUDMasterData que se puede importar y usar en los routers
master_data = CRUDMasterData(MasterData)
