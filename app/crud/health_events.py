# app/crud/health_events.py
from typing import Optional, List
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_

# Importa el modelo HealthEvent y AnimalHealthEventPivot, y los esquemas
from app.models.health_event import HealthEvent
from app.models.animal_health_event_pivot import AnimalHealthEventPivot
from app.schemas.health_event import HealthEventCreate, HealthEventUpdate
from app.schemas.animal_health_event_pivot import AnimalHealthEventPivotCreate

# Importa la CRUDBase y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException

class CRUDHealthEvent(CRUDBase[HealthEvent, HealthEventCreate, HealthEventUpdate]):
    """
    Clase CRUD específica para el modelo HealthEvent.
    Gestiona los eventos de salud y su asociación con animales.
    """

    async def create(self, db: AsyncSession, *, obj_in: HealthEventCreate, administered_by_user_id: uuid.UUID) -> HealthEvent:
        """
        Crea un nuevo evento de salud y asocia los animales especificados a través de la tabla pivot.
        """
        try:
            # Crear el evento de salud principal
            health_event_data = obj_in.model_dump(exclude={"animal_ids"})
            db_health_event = self.model(**health_event_data, administered_by_user_id=administered_by_user_id)
            db.add(db_health_event)
            await db.flush() # Para que db_health_event tenga un ID antes de crear pivotes

            # Crear entradas en la tabla pivot AnimalHealthEventPivot para cada animal
            for animal_id in obj_in.animal_ids:
                pivot_obj = AnimalHealthEventPivot(
                    animal_id=animal_id,
                    health_event_id=db_health_event.id
                )
                db.add(pivot_obj)

            await db.commit()
            await db.refresh(db_health_event)
            
            # Recarga el evento de salud con las relaciones (incluyendo los animales afectados)
            result = await db.execute(
                select(HealthEvent)
                .options(
                    selectinload(HealthEvent.animals_affected).selectinload(AnimalHealthEventPivot.animal),
                    selectinload(HealthEvent.product),
                    selectinload(HealthEvent.unit),
                    selectinload(HealthEvent.administered_by_user)
                )
                .filter(HealthEvent.id == db_health_event.id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating HealthEvent: {str(e)}") from e

    async def get(self, db: AsyncSession, health_event_id: uuid.UUID) -> Optional[HealthEvent]:
        """
        Obtiene un evento de salud por su ID, cargando las relaciones.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.animals_affected).selectinload(AnimalHealthEventPivot.animal),
                selectinload(self.model.product),
                selectinload(self.model.unit),
                selectinload(self.model.administered_by_user)
            )
            .filter(self.model.id == health_event_id)
        )
        return result.scalar_one_or_none()

    async def get_multi_by_animal_id(self, db: AsyncSession, animal_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[HealthEvent]:
        """
        Obtiene todos los eventos de salud asociados a un animal específico.
        """
        # Primero, encuentra los IDs de los eventos de salud a través de la tabla pivot
        pivot_results = await db.execute(
            select(AnimalHealthEventPivot.health_event_id)
            .filter(AnimalHealthEventPivot.animal_id == animal_id)
        )
        health_event_ids = pivot_results.scalars().all()

        if not health_event_ids:
            return [] # No hay eventos para este animal

        # Luego, obtén los eventos de salud usando esos IDs
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.animals_affected).selectinload(AnimalHealthEventPivot.animal),
                selectinload(self.model.product),
                selectinload(self.model.unit),
                selectinload(self.model.administered_by_user)
            )
            .filter(self.model.id.in_(health_event_ids))
            .order_by(self.model.event_date.desc()) # Ordenar por fecha de evento descendente
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, db: AsyncSession, *, db_obj: HealthEvent, obj_in: HealthEventUpdate) -> HealthEvent:
        """
        Actualiza un evento de salud existente.
        Nota: Este método NO actualiza las asociaciones de animales. Eso se manejaría
        a través de la creación/eliminación de entradas en AnimalHealthEventPivot directamente.
        """
        updated_event = await super().update(db, db_obj=db_obj, obj_in=obj_in)
        if updated_event:
            result = await db.execute(
                select(self.model)
                .options(
                    selectinload(self.model.animals_affected).selectinload(AnimalHealthEventPivot.animal),
                    selectinload(self.model.product),
                    selectinload(self.model.unit),
                    selectinload(self.model.administered_by_user)
                )
                .filter(self.model.id == updated_event.id)
            )
            return result.scalar_one_or_none()
        return updated_event

    async def delete(self, db: AsyncSession, *, id: uuid.UUID) -> HealthEvent:
        """
        Elimina un evento de salud por su ID.
        Debido a `cascade="all, delete-orphan"` en la relación `animals_affected`,
        las entradas de AnimalHealthEventPivot relacionadas se eliminarán automáticamente.
        """
        db_obj = await self.get(db, id) # Primero obtenemos el objeto para asegurar que existe y para devolverlo
        if not db_obj:
            raise NotFoundError(f"HealthEvent with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj # Retorna el objeto eliminado
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting HealthEvent: {str(e)}") from e

# Crea una instancia de CRUDHealthEvent que se puede importar y usar en los routers
health_event = CRUDHealthEvent(HealthEvent)
