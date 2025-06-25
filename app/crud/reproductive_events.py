# app/crud/reproductive_events.py
from typing import Optional, List, Union, Dict, Any # Añadido Union, Dict, Any
import uuid
from datetime import datetime, date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError as DBIntegrityError # Importa la excepción de integridad de SQLAlchemy


# Importa el modelo ReproductiveEvent y los esquemas
from app.models.reproductive_event import ReproductiveEvent
# También necesitamos importar el modelo Animal para las cargas eager y validación
from app.models.animal import Animal
# Y el modelo OffspringBorn si lo necesitas para cargas específicas del pivote
from app.models.offspring_born import OffspringBorn

from app.schemas.reproductive_event import ReproductiveEventCreate, ReproductiveEventUpdate

# Importa la CRUDBase y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, CRUDException, AlreadyExistsError # Añadido AlreadyExistsError

class CRUDReproductiveEvent(CRUDBase[ReproductiveEvent, ReproductiveEventCreate, ReproductiveEventUpdate]):
    """
    Clase CRUD específica para el modelo ReproductiveEvent.
    Gestiona los eventos reproductivos de los animales.
    """

    async def create(self, db: AsyncSession, *, obj_in: ReproductiveEventCreate, administered_by_user_id: uuid.UUID) -> ReproductiveEvent:
        """
        Crea un nuevo evento reproductivo.
        Valida la existencia del animal hembra y del semental (si se proporciona).
        """
        try:
            # Validar que el animal (hembra) existe
            animal_exists_q = await db.execute(select(Animal).filter(Animal.id == obj_in.animal_id))
            if not animal_exists_q.scalar_one_or_none():
                raise NotFoundError(f"Animal (female) with ID {obj_in.animal_id} not found.")

            # Validar que el semental existe si se proporciona
            if obj_in.sire_animal_id:
                sire_animal_exists_q = await db.execute(select(Animal).filter(Animal.id == obj_in.sire_animal_id))
                if not sire_animal_exists_q.scalar_one_or_none():
                    raise NotFoundError(f"Sire animal with ID {obj_in.sire_animal_id} not found.")

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
            return result.scalars().first()
        except DBIntegrityError as e:
            await db.rollback()
            raise AlreadyExistsError(f"Error de integridad al crear ReproductiveEvent: {e}") from e
        except Exception as e:
            await db.rollback()
            if isinstance(e, NotFoundError) or isinstance(e, AlreadyExistsError):
                raise e
            raise CRUDException(f"Error creating ReproductiveEvent: {str(e)}") from e

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[ReproductiveEvent]: # Cambiado event_id a id
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
            .filter(self.model.id == id) # Cambiado event_id a id
        )
        return result.scalars().first()

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

    async def update(self, db: AsyncSession, *, db_obj: ReproductiveEvent, obj_in: Union[ReproductiveEventUpdate, Dict[str, Any]]) -> ReproductiveEvent: # Añadido Union, Dict, Any
        """
        Actualiza un evento reproductivo existente.
        Valida la existencia del animal hembra y del semental (si se proporcionan y cambian).
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
                    raise NotFoundError(f"Animal (female) with ID {update_data['animal_id']} not found.")

            # Validar sire_animal_id si se proporciona y es diferente
            if "sire_animal_id" in update_data and update_data["sire_animal_id"] != db_obj.sire_animal_id:
                sire_animal_exists_q = await db.execute(select(Animal).filter(Animal.id == update_data["sire_animal_id"]))
                if not sire_animal_exists_q.scalar_one_or_none():
                    raise NotFoundError(f"Sire animal with ID {update_data['sire_animal_id']} not found.")

            updated_event = await super().update(db, db_obj=db_obj, obj_in=update_data)
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
                return result.scalars().first()
            return updated_event
        except Exception as e:
            await db.rollback()
            if isinstance(e, NotFoundError) or isinstance(e, AlreadyExistsError) or isinstance(e, CRUDException):
                raise e
            raise CRUDException(f"Error updating ReproductiveEvent: {str(e)}") from e

    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[ReproductiveEvent]: # Cambiado delete a remove
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
