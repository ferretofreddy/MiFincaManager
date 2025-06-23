# app/crud/reproductive_events.py
from typing import Optional, List
import uuid
from datetime import datetime, date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_

# Importa el modelo ReproductiveEvent y los esquemas
from app.models.reproductive_event import ReproductiveEvent
from app.schemas.reproductive_event import ReproductiveEventCreate, ReproductiveEventUpdate

# Importa la CRUDBase y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, CRUDException

class CRUDReproductiveEvent(CRUDBase[ReproductiveEvent, ReproductiveEventCreate, ReproductiveEventUpdate]):
    """
    Clase CRUD específica para el modelo ReproductiveEvent.
    Gestiona los eventos reproductivos de los animales.
    """

    async def create(self, db: AsyncSession, *, obj_in: ReproductiveEventCreate, administered_by_user_id: uuid.UUID) -> ReproductiveEvent:
        """
        Crea un nuevo evento reproductivo.
        """
        try:
            db_reproductive_event = self.model(**obj_in.model_dump(), administered_by_user_id=administered_by_user_id)
            db.add(db_reproductive_event)
            await db.commit()
            await db.refresh(db_reproductive_event)
            
            # Recarga el evento reproductivo con las relaciones
            result = await db.execute(
                select(ReproductiveEvent)
                .options(
                    selectinload(ReproductiveEvent.animal),
                    selectinload(ReproductiveEvent.sire_animal),
                    selectinload(ReproductiveEvent.administered_by_user),
                    selectinload(ReproductiveEvent.offspring_born_events) # Cargar también los eventos de nacimiento asociados
                )
                .filter(ReproductiveEvent.id == db_reproductive_event.id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating ReproductiveEvent: {str(e)}") from e

    async def get(self, db: AsyncSession, event_id: uuid.UUID) -> Optional[ReproductiveEvent]:
        """
        Obtiene un evento reproductivo por su ID, cargando las relaciones.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.sire_animal),
                selectinload(self.model.administered_by_user),
                selectinload(self.model.offspring_born_events)
            )
            .filter(self.model.id == event_id)
        )
        return result.scalar_one_or_none()

    async def get_multi_by_animal_id(self, db: AsyncSession, animal_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[ReproductiveEvent]:
        """
        Obtiene todos los eventos reproductivos de un animal específico (hembra).
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.sire_animal),
                selectinload(self.model.administered_by_user),
                selectinload(self.model.offspring_born_events)
            )
            .filter(self.model.animal_id == animal_id)
            .order_by(self.model.event_date.desc()) # Ordenar por fecha de evento descendente
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_multi_by_sire_animal_id(self, db: AsyncSession, sire_animal_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[ReproductiveEvent]:
        """
        Obtiene todos los eventos reproductivos donde un animal específico fue el semental.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.sire_animal),
                selectinload(self.model.administered_by_user),
                selectinload(self.model.offspring_born_events)
            )
            .filter(self.model.sire_animal_id == sire_animal_id)
            .order_by(self.model.event_date.desc()) # Ordenar por fecha de evento descendente
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, db: AsyncSession, *, db_obj: ReproductiveEvent, obj_in: ReproductiveEventUpdate) -> ReproductiveEvent:
        """
        Actualiza un evento reproductivo existente.
        """
        updated_event = await super().update(db, db_obj=db_obj, obj_in=obj_in)
        if updated_event:
            result = await db.execute(
                select(self.model)
                .options(
                    selectinload(self.model.animal),
                    selectinload(self.model.sire_animal),
                    selectinload(self.model.administered_by_user),
                    selectinload(self.model.offspring_born_events)
                )
                .filter(self.model.id == updated_event.id)
            )
            return result.scalar_one_or_none()
        return updated_event

    async def delete(self, db: AsyncSession, *, id: uuid.UUID) -> ReproductiveEvent:
        """
        Elimina un evento reproductivo por su ID.
        Debido a `cascade="all, delete-orphan"` en la relación `offspring_born_events`,
        las entradas de OffspringBorn relacionadas se eliminarán automáticamente.
        """
        db_obj = await self.get(db, id) # Primero obtenemos el objeto para asegurar que existe y para devolverlo
        if not db_obj:
            raise NotFoundError(f"ReproductiveEvent with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj # Retorna el objeto eliminado
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting ReproductiveEvent: {str(e)}") from e

# Crea una instancia de CRUDReproductiveEvent que se puede importar y usar en los routers
reproductive_event = CRUDReproductiveEvent(ReproductiveEvent)
