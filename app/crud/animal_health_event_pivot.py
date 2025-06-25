# app/crud/animal_health_event_pivot.py 
from typing import Optional, List, Union, Dict, Any
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError as DBIntegrityError

from app.models.animal_health_event_pivot import AnimalHealthEventPivot
from app.schemas.animal_health_event_pivot import AnimalHealthEventPivotCreate

from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException

# Nota: AnimalHealthEventPivotCreate es el CreateSchemaType. Como no hay un esquema Update,
# usamos 'None' para UpdateSchemaType en CRUDBase.
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
        Verifica si la asociación ya existe.
        """
        # Verificar si la asociación ya existe
        existing_association = await self.get_by_animal_and_event_id(db, obj_in.animal_id, obj_in.health_event_id)
        if existing_association:
            raise AlreadyExistsError(f"Animal {obj_in.animal_id} is already associated with Health Event {obj_in.health_event_id}.")

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
        except DBIntegrityError as e: # Captura errores de integridad de la DB
            await db.rollback()
            raise AlreadyExistsError(f"Association for animal {obj_in.animal_id} and health event {obj_in.health_event_id} already exists.") from e
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating AnimalHealthEventPivot: {str(e)}") from e

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[AnimalHealthEventPivot]:
        """
        Obtiene una asociación pivot por su ID, cargando las relaciones.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.health_event)
            )
            .filter(self.model.id == id)
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

    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[AnimalHealthEventPivot]:
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
