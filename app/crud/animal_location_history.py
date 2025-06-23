# app/crud/animal_location_history.py
from typing import Optional, List
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_

# Importa el modelo AnimalLocationHistory y los esquemas
from app.models.animal_location_history import AnimalLocationHistory
from app.schemas.animal_location_history import AnimalLocationHistoryCreate, AnimalLocationHistoryUpdate

# Importa la CRUDBase y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException

class CRUDAnimalLocationHistory(CRUDBase[AnimalLocationHistory, AnimalLocationHistoryCreate, AnimalLocationHistoryUpdate]):
    """
    Clase CRUD específica para el modelo AnimalLocationHistory.
    Gestiona el historial de ubicación de los animales en lotes.
    """

    async def create(self, db: AsyncSession, *, obj_in: AnimalLocationHistoryCreate, created_by_user_id: uuid.UUID) -> AnimalLocationHistory:
        """
        Crea una nueva entrada en el historial de ubicación de un animal.
        Puedes añadir lógica aquí para asegurar que no haya superposiciones de fechas
        o para cerrar una entrada anterior si el animal se mueve de lote.
        """
        # Opcional: Lógica para cerrar la ubicación anterior del animal si existe
        # Por ejemplo, si un animal solo puede estar en un lote activo a la vez:
        # existing_active_location = await db.execute(
        #     select(AnimalLocationHistory).filter(
        #         and_(AnimalLocationHistory.animal_id == obj_in.animal_id, AnimalLocationHistory.departure_date.is_(None))
        #     )
        # )
        # if existing_active_location.scalar_one_or_none():
        #     # Cierra la entrada anterior (actualiza departure_date)
        #     await self.update(db, db_obj=existing_active_location.scalar_one(), obj_in=AnimalLocationHistoryUpdate(departure_date=obj_in.entry_date))
        #     # Esto es una simplificación, la lógica real puede ser más compleja.

        try:
            db_obj = self.model(**obj_in.model_dump(), created_by_user_id=created_by_user_id)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            
            # Recarga la entrada del historial con las relaciones
            result = await db.execute(
                select(AnimalLocationHistory)
                .options(
                    selectinload(AnimalLocationHistory.animal),
                    selectinload(AnimalLocationHistory.lot),
                    selectinload(AnimalLocationHistory.created_by_user)
                )
                .filter(AnimalLocationHistory.id == db_obj.id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating AnimalLocationHistory: {str(e)}") from e

    async def get(self, db: AsyncSession, history_id: uuid.UUID) -> Optional[AnimalLocationHistory]:
        """
        Obtiene una entrada del historial de ubicación por su ID, cargando las relaciones.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.lot),
                selectinload(self.model.created_by_user)
            )
            .filter(self.model.id == history_id)
        )
        return result.scalar_one_or_none()

    async def get_by_compound_keys(self, db: AsyncSession, animal_id: uuid.UUID, lot_id: uuid.UUID, entry_date: datetime) -> Optional[AnimalLocationHistory]:
        """
        Obtiene una entrada del historial por sus claves compuestas (animal_id, lot_id, entry_date).
        Útil si aún necesitas esta forma de búsqueda y decides no usar el ID de BaseModel como PK única.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.lot),
                selectinload(self.model.created_by_user)
            )
            .filter(
                and_(
                    self.model.animal_id == animal_id,
                    self.model.lot_id == lot_id,
                    self.model.entry_date == entry_date
                )
            )
        )
        return result.scalar_one_or_none()


    async def get_multi_by_animal_id(self, db: AsyncSession, animal_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[AnimalLocationHistory]:
        """
        Obtiene todas las entradas del historial de ubicación para un animal específico.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.lot),
                selectinload(self.model.created_by_user)
            )
            .filter(self.model.animal_id == animal_id)
            .order_by(self.model.entry_date.desc()) # Ordenar por fecha de entrada descendente
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_multi_by_lot_id(self, db: AsyncSession, lot_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[AnimalLocationHistory]:
        """
        Obtiene todas las entradas del historial de ubicación para un lote específico.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.animal),
                selectinload(self.model.lot),
                selectinload(self.model.created_by_user)
            )
            .filter(self.model.lot_id == lot_id)
            .order_by(self.model.entry_date.desc()) # Ordenar por fecha de entrada descendente
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, db: AsyncSession, *, db_obj: AnimalLocationHistory, obj_in: AnimalLocationHistoryUpdate) -> AnimalLocationHistory:
        """
        Actualiza una entrada del historial de ubicación existente.
        Se usa principalmente para establecer 'departure_date'.
        """
        updated_history = await super().update(db, db_obj=db_obj, obj_in=obj_in)
        if updated_history:
            result = await db.execute(
                select(self.model)
                .options(
                    selectinload(self.model.animal),
                    selectinload(self.model.lot),
                    selectinload(self.model.created_by_user)
                )
                .filter(self.model.id == updated_history.id)
            )
            return result.scalar_one_or_none()
        return updated_history

# Crea una instancia de CRUDAnimalLocationHistory que se puede importar y usar en los routers
animal_location_history = CRUDAnimalLocationHistory(AnimalLocationHistory)
