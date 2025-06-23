# app/crud/weighings.py
from typing import Optional, List
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_

# Importa el modelo Weighing y los esquemas
from app.models.weighing import Weighing
from app.schemas.weighing import WeighingCreate, WeighingUpdate

# Importa la CRUDBase y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, CRUDException

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
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating Weighing record: {str(e)}") from e

    async def get(self, db: AsyncSession, weighing_id: uuid.UUID) -> Optional[Weighing]:
        """
        Obtiene un registro de pesaje por su ID, cargando las relaciones.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.recorded_by_user)
            )
            .filter(self.model.id == weighing_id)
        )
        return result.scalar_one_or_none()

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

    async def update(self, db: AsyncSession, *, db_obj: Weighing, obj_in: WeighingUpdate) -> Weighing:
        """
        Actualiza un registro de pesaje existente.
        """
        updated_weighing = await super().update(db, db_obj=db_obj, obj_in=obj_in)
        if updated_weighing:
            result = await db.execute(
                select(self.model)
                .options(
                    selectinload(self.model.animal),
                    selectinload(self.model.recorded_by_user)
                )
                .filter(self.model.id == updated_weighing.id)
            )
            return result.scalar_one_or_none()
        return updated_weighing

    async def delete(self, db: AsyncSession, *, id: uuid.UUID) -> Weighing:
        """
        Elimina un registro de pesaje por su ID.
        """
        db_obj = await self.get(db, id)
        if not db_obj:
            raise NotFoundError(f"Weighing record with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj # Retorna el objeto eliminado
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting Weighing record: {str(e)}") from e

# Crea una instancia de CRUDWeighing que se puede importar y usar en los routers
weighing = CRUDWeighing(Weighing)
