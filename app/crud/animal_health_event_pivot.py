# app/crud/animal_health_event_pivot.py
from typing import Optional, List
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_

# Importa el modelo AnimalHealthEventPivot y los esquemas
from app.models.animal_health_event_pivot import AnimalHealthEventPivot
from app.schemas.animal_health_event_pivot import AnimalHealthEventPivotCreate # No hay update usualmente para pivotes simples

# Importa la CRUDBase y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException

class CRUDAnimalHealthEventPivot(CRUDBase[AnimalHealthEventPivot, AnimalHealthEventPivotCreate, None]):
    """
    Clase CRUD específica para el modelo AnimalHealthEventPivot.
    Gestiona las asociaciones directas entre Animales y Eventos de Salud.
    No se usa un 'UpdateSchemaType' ya que las entradas de pivote rara vez se "actualizan" en el sentido tradicional,
    sino que se crean o eliminan.
    """

    async def create(self, db: AsyncSession, *, obj_in: AnimalHealthEventPivotCreate) -> AnimalHealthEventPivot:
        """
        Crea una nueva asociación entre un animal y un evento de salud.
        """
        try:
            db_obj = self.model(**obj_in.model_dump())
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            
            # Recarga la asociación con las relaciones
            result = await db.execute(
                select(AnimalHealthEventPivot)
                .options(
                    selectinload(AnimalHealthEventPivot.animal),
                    selectinload(AnimalHealthEventPivot.health_event)
                )
                .filter(AnimalHealthEventPivot.id == db_obj.id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating AnimalHealthEventPivot: {str(e)}") from e

    async def get(self, db: AsyncSession, pivot_id: uuid.UUID) -> Optional[AnimalHealthEventPivot]:
        """
        Obtiene una asociación pivot por su ID, cargando las relaciones.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.health_event)
            )
            .filter(self.model.id == pivot_id)
        )
        return result.scalar_one_or_none()

    async def get_by_animal_and_event_id(self, db: AsyncSession, animal_id: uuid.UUID, health_event_id: uuid.UUID) -> Optional[AnimalHealthEventPivot]:
        """
        Obtiene una asociación pivot por los IDs del animal y del evento de salud.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.health_event)
            )
            .filter(
                and_(
                    self.model.animal_id == animal_id,
                    self.model.health_event_id == health_event_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_multi_by_animal_id(self, db: AsyncSession, animal_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[AnimalHealthEventPivot]:
        """
        Obtiene todas las asociaciones pivot para un animal específico.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.health_event)
            )
            .filter(self.model.animal_id == animal_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_multi_by_health_event_id(self, db: AsyncSession, health_event_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[AnimalHealthEventPivot]:
        """
        Obtiene todas las asociaciones pivot para un evento de salud específico.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.health_event)
            )
            .filter(self.model.health_event_id == health_event_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def delete(self, db: AsyncSession, *, id: uuid.UUID) -> AnimalHealthEventPivot:
        """
        Elimina una asociación pivot por su ID.
        """
        db_obj = await self.get(db, id)
        if not db_obj:
            raise NotFoundError(f"AnimalHealthEventPivot with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting AnimalHealthEventPivot: {str(e)}") from e

# Crea una instancia de CRUDAnimalHealthEventPivot que se puede importar y usar
animal_health_event_pivot = CRUDAnimalHealthEventPivot(AnimalHealthEventPivot)
