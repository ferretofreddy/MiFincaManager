# app/crud/animal_location_history.py
from typing import Optional, List, Union, Dict, Any
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError as DBIntegrityError

from app.models.animal_location_history import AnimalLocationHistory
from app.schemas.animal_location_history import AnimalLocationHistoryCreate, AnimalLocationHistoryUpdate

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
        # existing_active_location_query = await db.execute(
        #     select(AnimalLocationHistory).filter(
        #         and_(AnimalLocationHistory.animal_id == obj_in.animal_id, AnimalLocationHistory.departure_date.is_(None))
        #     )
        # )
        # existing_active_location = existing_active_location_query.scalars().first()
        # if existing_active_location:
        #     # Cierra la entrada anterior (actualiza departure_date)
        #     # Asegúrate de que obj_in.entry_date sea una fecha válida para el cierre
        #     update_data = {"departure_date": obj_in.entry_date}
        #     await self.update(db, db_obj=existing_active_location, obj_in=update_data)
        #     # Esto es una simplificación, la lógica real puede ser más compleja
        #     # como verificar que entry_date de la nueva entrada sea posterior a la de la anterior.

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
        except DBIntegrityError as e:
            await db.rollback()
            raise AlreadyExistsError(f"Error de integridad al crear AnimalLocationHistory: {e}") from e
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating AnimalLocationHistory: {str(e)}") from e

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[AnimalLocationHistory]:
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
            .filter(self.model.id == id)
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
            .order_by(self.model.entry_date.desc())
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
            .order_by(self.model.entry_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, db: AsyncSession, *, db_obj: AnimalLocationHistory, obj_in: Union[AnimalLocationHistoryUpdate, Dict[str, Any]]) -> AnimalLocationHistory:
        """
        Actualiza una entrada del historial de ubicación existente.
        Se usa principalmente para establecer 'departure_date'.
        """
        try:
            # Si obj_in es un Pydantic model, conviértelo a dict y excluye unset
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)

            updated_history = await super().update(db, db_obj=db_obj, obj_in=update_data)
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
                return result.scalars().first()
            return updated_history
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error updating AnimalLocationHistory: {str(e)}") from e

    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[AnimalLocationHistory]:
        """
        Elimina una entrada del historial de ubicación por su ID.
        """
        db_obj = await self.get(db, id)
        if not db_obj:
            raise NotFoundError(f"AnimalLocationHistory with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting AnimalLocationHistory: {str(e)}") from e

animal_location_history = CRUDAnimalLocationHistory(AnimalLocationHistory)
