# app/crud/offspring_born.py
from typing import Optional, List, Union, Dict, Any # Añadido Union, Dict, Any
import uuid
from datetime import datetime, date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError as DBIntegrityError # Importa la excepción de integridad de SQLAlchemy


# Importa el modelo OffspringBorn y los esquemas
from app.models.offspring_born import OffspringBorn
# Si vas a validar que los IDs existan, también necesitarías importar Animal y ReproductiveEvent
from app.models.animal import Animal # Importado para validación
from app.models.reproductive_event import ReproductiveEvent # Importado para validación
from app.schemas.offspring_born import OffspringBornCreate, OffspringBornUpdate

# Importa la CRUDBase y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, CRUDException, AlreadyExistsError # Añadido AlreadyExistsError

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
            # Validar que reproductive_event_id exista
            if obj_in.reproductive_event_id:
                reproductive_event_exists_q = await db.execute(select(ReproductiveEvent).filter(ReproductiveEvent.id == obj_in.reproductive_event_id))
                if not reproductive_event_exists_q.scalar_one_or_none():
                    raise NotFoundError(f"Reproductive event with ID {obj_in.reproductive_event_id} not found.")
            
            # Validar que offspring_animal_id exista (si se proporciona)
            if obj_in.offspring_animal_id:
                offspring_animal_exists_q = await db.execute(select(Animal).filter(Animal.id == obj_in.offspring_animal_id))
                if not offspring_animal_exists_q.scalar_one_or_none():
                    raise NotFoundError(f"Offspring animal with ID {obj_in.offspring_animal_id} not found.")

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
            return result.scalars().first()
        except DBIntegrityError as e:
            await db.rollback()
            raise AlreadyExistsError(f"Error de integridad al crear OffspringBorn record: {e}") from e
        except Exception as e:
            await db.rollback()
            # Si es un NotFoundError (de las validaciones opcionales), relanzarlo.
            if isinstance(e, NotFoundError) or isinstance(e, AlreadyExistsError):
                raise e
            raise CRUDException(f"Error creating OffspringBorn record: {str(e)}") from e

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[OffspringBorn]: # Cambiado offspring_born_id a id
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
            .filter(self.model.id == id) # Cambiado offspring_born_id a id
        )
        return result.scalars().first()

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

    async def update(self, db: AsyncSession, *, db_obj: OffspringBorn, obj_in: Union[OffspringBornUpdate, Dict[str, Any]]) -> OffspringBorn: # Añadido Union, Dict, Any
        """
        Actualiza un registro de cría nacida existente.
        """
        try:
            # Si obj_in es un Pydantic model, conviértelo a dict y excluye unset
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)

            # Validar claves foráneas si se proporcionan en la actualización
            if "reproductive_event_id" in update_data and update_data["reproductive_event_id"] != db_obj.reproductive_event_id:
                reproductive_event_exists_q = await db.execute(select(ReproductiveEvent).filter(ReproductiveEvent.id == update_data["reproductive_event_id"]))
                if not reproductive_event_exists_q.scalar_one_or_none():
                    raise NotFoundError(f"Reproductive event with ID {update_data['reproductive_event_id']} not found.")
            
            if "offspring_animal_id" in update_data and update_data["offspring_animal_id"] != db_obj.offspring_animal_id:
                offspring_animal_exists_q = await db.execute(select(Animal).filter(Animal.id == update_data["offspring_animal_id"]))
                if not offspring_animal_exists_q.scalar_one_or_none():
                    raise NotFoundError(f"Offspring animal with ID {update_data['offspring_animal_id']} not found.")

            updated_offspring = await super().update(db, db_obj=db_obj, obj_in=update_data)
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
                return result.scalars().first()
            return updated_offspring
        except Exception as e:
            await db.rollback()
            if isinstance(e, NotFoundError) or isinstance(e, AlreadyExistsError) or isinstance(e, CRUDException):
                raise e
            raise CRUDException(f"Error updating OffspringBorn record: {str(e)}") from e

    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[OffspringBorn]: # Cambiado delete a remove
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
