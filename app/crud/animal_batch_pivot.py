# app/crud/animal_batch_pivot.py
from typing import Optional, List
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_

# Importa el modelo AnimalBatchPivot y los esquemas
from app.models.animal_batch_pivot import AnimalBatchPivot
from app.schemas.animal_batch_pivot import AnimalBatchPivotCreate

# Importa las excepciones
from app.crud.exceptions import NotFoundError, CRUDException

class CRUDAnimalBatchPivot:
    """
    Clase CRUD específica para el modelo AnimalBatchPivot.
    Gestiona las asociaciones entre animales y lotes.
    Las operaciones de creación/actualización principales se esperan a través de CRUDBatch.
    """
    def __init__(self, model):
        self.model = model

    async def create(self, db: AsyncSession, *, obj_in: AnimalBatchPivotCreate) -> AnimalBatchPivot:
        """
        Crea una nueva asociación en la tabla pivote AnimalBatchPivot.
        """
        try:
            db_pivot = self.model(**obj_in.model_dump())
            db.add(db_pivot)
            await db.commit()
            await db.refresh(db_pivot)
            # Recargar con relaciones para la respuesta si se desea un objeto completo
            reloaded_obj = await self.get(db, db_pivot.animal_id, db_pivot.batch_event_id)
            return reloaded_obj if reloaded_obj else db_pivot
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating AnimalBatchPivot record: {str(e)}") from e

    async def get(self, db: AsyncSession, animal_id: uuid.UUID, batch_event_id: uuid.UUID) -> Optional[AnimalBatchPivot]:
        """
        Obtiene una asociación de pivote por sus IDs compuestos (animal_id, batch_event_id).
        """
        result = await db.execute(
            select(self.model)
            .filter(and_(
                self.model.animal_id == animal_id,
                self.model.batch_event_id == batch_event_id
            ))
            .options(
                selectinload(self.model.animal), # Opcional: Cargar relaciones si se necesitan
                selectinload(self.model.batch_event)
            )
        )
        return result.scalar_one_or_none()

    async def get_multi_by_animal_id(self, db: AsyncSession, animal_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[AnimalBatchPivot]:
        """
        Obtiene todas las asociaciones de pivote para un animal específico.
        """
        result = await db.execute(
            select(self.model)
            .filter(self.model.animal_id == animal_id)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.batch_event)
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_multi_by_batch_event_id(self, db: AsyncSession, batch_event_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[AnimalBatchPivot]:
        """
        Obtiene todas las asociaciones de pivote para un evento de lote específico.
        """
        result = await db.execute(
            select(self.model)
            .filter(self.model.batch_event_id == batch_event_id)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.batch_event)
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def delete(self, db: AsyncSession, animal_id: uuid.UUID, batch_event_id: uuid.UUID) -> AnimalBatchPivot:
        """
        Elimina una asociación de pivote específica por sus IDs compuestos.
        """
        db_obj = await self.get(db, animal_id, batch_event_id)
        if not db_obj:
            raise NotFoundError(f"AnimalBatchPivot association for Animal ID {animal_id} and Batch Event ID {batch_event_id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj # Retorna el objeto eliminado
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting AnimalBatchPivot record: {str(e)}") from e

# Crea una instancia de CRUDAnimalBatchPivot que se puede importar y usar
animal_batch_pivot = CRUDAnimalBatchPivot(AnimalBatchPivot)
