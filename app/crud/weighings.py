# app/crud/weighings.py
from typing import Optional, List, Union, Dict, Any # Añadido Union, Dict, Any
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError as DBIntegrityError # Importa la excepción de integridad de SQLAlchemy

# Importa el modelo Weighing y los esquemas
from app.models.weighing import Weighing
from app.models.animal import Animal # Importado para validación
from app.schemas.weighing import WeighingCreate, WeighingUpdate

# Importa la CRUDBase y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, CRUDException, AlreadyExistsError # Añadido AlreadyExistsError

class CRUDWeighing(CRUDBase[Weighing, WeighingCreate, WeighingUpdate]):
    """
    Clase CRUD específica para el modelo Weighing.
    Gestiona los registros de pesajes de animales.
    """

    async def create(self, db: AsyncSession, *, obj_in: WeighingCreate, recorded_by_user_id: uuid.UUID) -> Weighing:
        """
        Crea un nuevo registro de pesaje para un animal.
        """
        try:
            # Validar que animal_id exista
            animal_exists_q = await db.execute(select(Animal).filter(Animal.id == obj_in.animal_id))
            if not animal_exists_q.scalar_one_or_none():
                raise NotFoundError(f"Animal with ID {obj_in.animal_id} not found.")

            db_weighing = self.model(**obj_in.model_dump(), recorded_by_user_id=recorded_by_user_id)
            db.add(db_weighing)
            await db.commit()
            await db.refresh(db_weighing)
            
            # Recarga el registro de pesaje con las relaciones
            result = await db.execute(
                select(Weighing)
                .options(
                    selectinload(Weighing.animal),
                    selectinload(Weighing.recorded_by_user)
                )
                .filter(Weighing.id == db_weighing.id)
            )
            return result.scalars().first()
        except DBIntegrityError as e:
            await db.rollback()
            raise AlreadyExistsError(f"Error de integridad al crear Weighing record: {e}") from e
        except Exception as e:
            await db.rollback()
            if isinstance(e, NotFoundError) or isinstance(e, AlreadyExistsError):
                raise e
            raise CRUDException(f"Error creating Weighing record: {str(e)}") from e

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[Weighing]: # Cambiado weighing_id a id
        """
        Obtiene un registro de pesaje por su ID, cargando las relaciones.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.recorded_by_user)
            )
            .filter(self.model.id == id) # Cambiado weighing_id a id
        )
        return result.scalars().first()

    async def get_multi_by_animal_id(self, db: AsyncSession, animal_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Weighing]:
        """
        Obtiene todos los registros de pesaje para un animal específico.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.recorded_by_user)
            )
            .filter(self.model.animal_id == animal_id)
            .order_by(self.model.weighing_date.desc()) # Ordenar por fecha de pesaje descendente
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, db: AsyncSession, *, db_obj: Weighing, obj_in: Union[WeighingUpdate, Dict[str, Any]]) -> Weighing: # Añadido Union, Dict, Any
        """
        Actualiza un registro de pesaje existente.
        """
        try:
            # Si obj_in es un Pydantic model, conviértelo a dict y excluye unset
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)

            # Validar animal_id si se proporciona y es diferente
            if "animal_id" in update_data and update_data["animal_id"] != db_obj.animal_id:
                animal_exists_q = await db.execute(select(Animal).filter(Animal.id == update_data["animal_id"]))
                if not animal_exists_q.scalar_one_or_none():
                    raise NotFoundError(f"Animal with ID {update_data['animal_id']} not found.")

            updated_weighing = await super().update(db, db_obj=db_obj, obj_in=update_data)
            if updated_weighing:
                result = await db.execute(
                    select(self.model)
                    .options(
                        selectinload(self.model.animal),
                        selectinload(self.model.recorded_by_user)
                    )
                    .filter(self.model.id == updated_weighing.id)
                )
                return result.scalars().first()
            return updated_weighing
        except Exception as e:
            await db.rollback()
            if isinstance(e, NotFoundError) or isinstance(e, AlreadyExistsError) or isinstance(e, CRUDException):
                raise e
            raise CRUDException(f"Error updating Weighing record: {str(e)}") from e

    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[Weighing]: # Cambiado delete a remove
        """
        Elimina un registro de pesaje por su ID.
        """
        db_obj = await self.get(db, id)
        if not db_obj:
            raise NotFoundError(f"Weighing record with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting Weighing record: {str(e)}") from e

# Crea una instancia de CRUDWeighing que se puede importar y usar en los routers
weighing = CRUDWeighing(Weighing)
