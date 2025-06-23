# app/crud/offspring_born.py
from typing import Optional, List
import uuid
from datetime import datetime, date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_

# Importa el modelo OffspringBorn y los esquemas
from app.models.offspring_born import OffspringBorn
from app.schemas.offspring_born import OffspringBornCreate, OffspringBornUpdate

# Importa la CRUDBase y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, CRUDException

class CRUDOffspringBorn(CRUDBase[OffspringBorn, OffspringBornCreate, OffspringBornUpdate]):
    """
    Clase CRUD específica para el modelo OffspringBorn.
    Gestiona los registros de crías nacidas asociadas a eventos reproductivos.
    """

    async def create(self, db: AsyncSession, *, obj_in: OffspringBornCreate, born_by_user_id: uuid.UUID) -> OffspringBorn:
        """
        Crea un nuevo registro de cría nacida.
        """
        try:
            db_offspring_born = self.model(**obj_in.model_dump(), born_by_user_id=born_by_user_id)
            db.add(db_offspring_born)
            await db.commit()
            await db.refresh(db_offspring_born)
            
            # Recarga el registro de nacimiento con las relaciones
            result = await db.execute(
                select(OffspringBorn)
                .options(
                    selectinload(OffspringBorn.reproductive_event),
                    selectinload(OffspringBorn.offspring_animal),
                    selectinload(OffspringBorn.born_by_user)
                )
                .filter(OffspringBorn.id == db_offspring_born.id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating OffspringBorn record: {str(e)}") from e

    async def get(self, db: AsyncSession, offspring_born_id: uuid.UUID) -> Optional[OffspringBorn]:
        """
        Obtiene un registro de cría nacida por su ID, cargando las relaciones.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.reproductive_event),
                selectinload(self.model.offspring_animal),
                selectinload(self.model.born_by_user)
            )
            .filter(self.model.id == offspring_born_id)
        )
        return result.scalar_one_or_none()

    async def get_multi_by_reproductive_event_id(self, db: AsyncSession, reproductive_event_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[OffspringBorn]:
        """
        Obtiene todos los registros de crías nacidas asociados a un evento reproductivo específico.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.reproductive_event),
                selectinload(self.model.offspring_animal),
                selectinload(self.model.born_by_user)
            )
            .filter(self.model.reproductive_event_id == reproductive_event_id)
            .order_by(self.model.date_of_birth.desc()) # Ordenar por fecha de nacimiento descendente
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_multi_by_animal_id(self, db: AsyncSession, animal_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[OffspringBorn]:
        """
        Obtiene todos los registros de crías nacidas donde un animal específico es la cría.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.reproductive_event),
                selectinload(self.model.offspring_animal),
                selectinload(self.model.born_by_user)
            )
            .filter(self.model.offspring_animal_id == animal_id)
            .order_by(self.model.date_of_birth.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, db: AsyncSession, *, db_obj: OffspringBorn, obj_in: OffspringBornUpdate) -> OffspringBorn:
        """
        Actualiza un registro de cría nacida existente.
        """
        updated_offspring = await super().update(db, db_obj=db_obj, obj_in=obj_in)
        if updated_offspring:
            result = await db.execute(
                select(self.model)
                .options(
                    selectinload(self.model.reproductive_event),
                    selectinload(self.model.offspring_animal),
                    selectinload(self.model.born_by_user)
                )
                .filter(self.model.id == updated_offspring.id)
            )
            return result.scalar_one_or_none()
        return updated_offspring

    async def delete(self, db: AsyncSession, *, id: uuid.UUID) -> OffspringBorn:
        """
        Elimina un registro de cría nacida por su ID.
        """
        db_obj = await self.get(db, id)
        if not db_obj:
            raise NotFoundError(f"OffspringBorn record with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting OffspringBorn record: {str(e)}") from e

# Crea una instancia de CRUDOffspringBorn que se puede importar y usar
offspring_born = CRUDOffspringBorn(OffspringBorn)
