# app/crud/animal_feeding_pivot.py
from typing import Optional, List
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError as DBIntegrityError

from app.models.animal_feeding_pivot import AnimalFeedingPivot
from app.schemas.animal_feeding_pivot import AnimalFeedingPivotCreate

from app.crud.exceptions import NotFoundError, CRUDException, AlreadyExistsError

class CRUDAnimalFeedingPivot:
    """
    Clase CRUD específica para el modelo AnimalFeedingPivot.
    Gestiona las asociaciones entre animales y eventos de alimentación.
    Las operaciones de creación/actualización principales se esperan a través de CRUDFeeding.
    """
    def __init__(self, model):
        self.model = model

    async def create(self, db: AsyncSession, *, obj_in: AnimalFeedingPivotCreate) -> AnimalFeedingPivot:
        """
        Crea una nueva asociación en la tabla pivote AnimalFeedingPivot.
        Verifica si la asociación ya existe antes de crearla.
        """
        # Verificar si la asociación ya existe
        existing_association = await self.get(db, obj_in.animal_id, obj_in.feeding_event_id)
        if existing_association:
            raise AlreadyExistsError(f"Animal {obj_in.animal_id} is already associated with Feeding Event {obj_in.feeding_event_id}.")

        try:
            db_pivot = self.model(**obj_in.model_dump())
            db.add(db_pivot)
            await db.commit()
            await db.refresh(db_pivot)
            # Recargar con relaciones para la respuesta si se desea un objeto completo
            reloaded_obj = await self.get(db, db_pivot.animal_id, db_pivot.feeding_event_id)
            return reloaded_obj if reloaded_obj else db_pivot
        except DBIntegrityError as e: # Captura errores de integridad de la DB
            await db.rollback()
            raise AlreadyExistsError(f"Association for animal {obj_in.animal_id} and feeding event {obj_in.feeding_event_id} already exists.") from e
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating AnimalFeedingPivot record: {str(e)}") from e

    async def get(self, db: AsyncSession, animal_id: uuid.UUID, feeding_event_id: uuid.UUID) -> Optional[AnimalFeedingPivot]:
        """
        Obtiene una asociación de pivote por sus IDs compuestos (animal_id, feeding_event_id).
        """
        result = await db.execute(
            select(self.model)
            .filter(and_(
                self.model.animal_id == animal_id,
                self.model.feeding_event_id == feeding_event_id
            ))
            .options(
                selectinload(self.model.animal), # Opcional: Cargar relaciones si se necesitan
                selectinload(self.model.feeding_event)
            )
        )
        return result.scalar_one_or_none()

    async def get_multi_by_animal_id(self, db: AsyncSession, animal_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[AnimalFeedingPivot]:
        """
        Obtiene todas las asociaciones de pivote para un animal específico.
        """
        result = await db.execute(
            select(self.model)
            .filter(self.model.animal_id == animal_id)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.feeding_event)
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_multi_by_feeding_event_id(self, db: AsyncSession, feeding_event_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[AnimalFeedingPivot]:
        """
        Obtiene todas las asociaciones de pivote para un evento de alimentación específico.
        """
        result = await db.execute(
            select(self.model)
            .filter(self.model.feeding_event_id == feeding_event_id)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.feeding_event)
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def remove(self, db: AsyncSession, animal_id: uuid.UUID, feeding_event_id: uuid.UUID) -> AnimalFeedingPivot:
        """
        Elimina una asociación de pivote específica por sus IDs compuestos.
        """
        db_obj = await self.get(db, animal_id, feeding_event_id)
        if not db_obj:
            raise NotFoundError(f"AnimalFeedingPivot association for Animal ID {animal_id} and Feeding Event ID {feeding_event_id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj # Retorna el objeto eliminado
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting AnimalFeedingPivot record: {str(e)}") from e

# Crea una instancia de CRUDAnimalFeedingPivot que se puede importar y usar
animal_feeding_pivot = CRUDAnimalFeedingPivot(AnimalFeedingPivot)
