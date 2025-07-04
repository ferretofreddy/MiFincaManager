# app/crud/feedings.py
from typing import Optional, List, Union, Dict, Any # Añadido Union, Dict, Any
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import and_, delete # Importado delete para el _remove_animal_associations
from sqlalchemy.exc import IntegrityError as DBIntegrityError # Importa la excepción de integridad de SQLAlchemy


# Importa el modelo Feeding y los esquemas
from app.models.feeding import Feeding
from app.models.animal import Animal # Necesario para validar animales
from app.models.master_data import MasterData # Necesario para validar MasterData
from app.models.animal_feeding_pivot import AnimalFeedingPivot # Necesario para gestionar pivotes

from app.schemas.feeding import FeedingCreate, FeedingUpdate
from app.schemas.animal_feeding_pivot import AnimalFeedingPivotCreate # Aunque no se use directamente, es bueno tener el contexto

# Importa la CRUDBase y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, CRUDException, AlreadyExistsError # Añadido AlreadyExistsError

class CRUDFeeding(CRUDBase[Feeding, FeedingCreate, FeedingUpdate]):
    """
    Clase CRUD específica para el modelo Feeding.
    Gestiona los eventos de alimentación, incluyendo la asociación con animales.
    """

    async def _add_animal_associations(self, db: AsyncSession, feeding_event_id: uuid.UUID, animal_ids: List[uuid.UUID]):
        """
        Añade asociaciones entre un evento de alimentación y una lista de animales.
        """
        for animal_id in animal_ids:
            # Verificar si la asociación ya existe para evitar duplicados
            existing_pivot_q = await db.execute(
                select(AnimalFeedingPivot)
                .filter(and_(
                    AnimalFeedingPivot.animal_id == animal_id,
                    AnimalFeedingPivot.feeding_event_id == feeding_event_id
                ))
            )
            existing_pivot = existing_pivot_q.scalar_one_or_none()

            if not existing_pivot:
                pivot_data = AnimalFeedingPivotCreate(
                    animal_id=animal_id,
                    feeding_event_id=feeding_event_id,
                    quantity_fed=None, # Opcional, se puede añadir lógica para calcular/pasar
                    notes="Automáticamente asociado durante la creación de la alimentación."
                )
                db_pivot = AnimalFeedingPivot(**pivot_data.model_dump())
                db.add(db_pivot)
        await db.flush() # Flush para que las asociaciones se creen antes de refresh

    async def _remove_animal_associations(self, db: AsyncSession, feeding_event_id: uuid.UUID, animal_ids_to_remove: List[uuid.UUID]):
        """
        Remueve asociaciones entre un evento de alimentación y una lista de animales.
        """
        # SQLAlchemy 2.0+ recomienda delete() con synchronize_session=False para eliminar múltiples
        # Si tienes problemas, podrías iterar y eliminar individualmente, pero esta es la forma performante.
        await db.execute(
            delete(AnimalFeedingPivot) # Usar delete directamente en la tabla
            .where(
                and_(
                    AnimalFeedingPivot.feeding_event_id == feeding_event_id,
                    AnimalFeedingPivot.animal_id.in_(animal_ids_to_remove) # animal_ids_to_remove ya es una lista de UUIDs
                )
            )
        )
        await db.flush() # Flush para que los cambios sean visibles en la transacción

    async def create(self, db: AsyncSession, *, obj_in: FeedingCreate, recorded_by_user_id: uuid.UUID) -> Feeding:
        """
        Crea un nuevo evento de alimentación y asocia los animales especificados.
        """
        try:
            # 1. Validar feed_type_id y unit_id como MasterData
            feed_type_md_q = await db.execute(select(MasterData).filter(MasterData.id == obj_in.feed_type_id))
            feed_type_md = feed_type_md_q.scalar_one_or_none()
            if not feed_type_md:
                raise NotFoundError(f"MasterData with ID {obj_in.feed_type_id} for feed type not found.")
            # Puedes añadir una validación de categoría si 'feed_type' debe ser de una categoría específica.
            # if feed_type_md.category != "feed_type_category":
            #     raise CRUDException("Invalid category for feed_type_id.")

            unit_md_q = await db.execute(select(MasterData).filter(MasterData.id == obj_in.unit_id))
            unit_md = unit_md_q.scalar_one_or_none()
            if not unit_md:
                raise NotFoundError(f"MasterData with ID {obj_in.unit_id} for unit not found.")
            # Puedes añadir una validación de categoría si 'unit' debe ser de una categoría específica.
            # if unit_md.category != "unit_category":
            #     raise CRUDException("Invalid category for unit_id.")

            # Crear el evento de alimentación principal
            feeding_data = obj_in.model_dump(exclude={"animal_ids"})
            db_feeding = self.model(**feeding_data, recorded_by_user_id=recorded_by_user_id)
            db.add(db_feeding)
            await db.flush() # Flush para obtener el ID del nuevo evento de alimentación

            # 2. Asociar animales si se proporcionan
            if obj_in.animal_ids:
                # Validar que los animales existen
                for animal_id in obj_in.animal_ids:
                    existing_animal_q = await db.execute(select(Animal).filter(Animal.id == animal_id))
                    if not existing_animal_q.scalar_one_or_none():
                        raise NotFoundError(f"Animal with ID {animal_id} not found. Cannot associate with feeding event.")
                
                await self._add_animal_associations(db, db_feeding.id, obj_in.animal_ids)
            
            await db.commit()
            await db.refresh(db_feeding) # Refresh final después de todas las operaciones

            # Recargar el evento de alimentación con todas las relaciones, incluyendo los pivotes
            result = await db.execute(
                select(Feeding)
                .options(
                    selectinload(Feeding.feed_type),
                    selectinload(Feeding.unit),
                    selectinload(Feeding.recorded_by_user),
                    selectinload(Feeding.animal_feedings).selectinload(AnimalFeedingPivot.animal) # Cargar también los animales asociados
                )
                .filter(Feeding.id == db_feeding.id)
            )
            return result.scalars().first() # Usar first() para consistencia
        except DBIntegrityError as e: # Captura errores de integridad de la DB
            await db.rollback()
            raise AlreadyExistsError(f"Error de integridad al crear Feeding event: {e}") from e
        except Exception as e:
            await db.rollback()
            # Si es un NotFoundError que lanzamos, relanzarlo. Si es otro error, envolverlo.
            if isinstance(e, NotFoundError) or isinstance(e, AlreadyExistsError):
                raise e
            raise CRUDException(f"Error creating Feeding event: {str(e)}") from e

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[Feeding]: # Cambiado feeding_id a id
        """
        Obtiene un evento de alimentación por su ID, cargando las relaciones.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.feed_type),
                selectinload(self.model.unit),
                selectinload(self.model.recorded_by_user),
                selectinload(self.model.animal_feedings).selectinload(AnimalFeedingPivot.animal)
            )
            .filter(self.model.id == id) # Cambiado feeding_id a id
        )
        return result.scalars().first() # Usar first() para consistencia

    async def get_multi_by_animal_id(self, db: AsyncSession, animal_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Feeding]:
        """
        Obtiene todos los eventos de alimentación asociados a un animal específico.
        """
        # Unimos a la tabla de pivote para filtrar por animal_id
        result = await db.execute(
            select(self.model)
            .join(AnimalFeedingPivot)
            .filter(AnimalFeedingPivot.animal_id == animal_id)
            .options(
                selectinload(self.model.feed_type),
                selectinload(self.model.unit),
                selectinload(self.model.recorded_by_user),
                selectinload(self.model.animal_feedings).selectinload(AnimalFeedingPivot.animal)
            )
            .order_by(self.model.feeding_date.desc()) # Ordenar por fecha de alimentación descendente
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().unique().all() # .unique() para evitar duplicados si un animal está en varios pivotes

    async def update(self, db: AsyncSession, *, db_obj: Feeding, obj_in: Union[FeedingUpdate, Dict[str, Any]]) -> Feeding: # Añadido Union, Dict, Any
        """
        Actualiza un evento de alimentación existente y sus asociaciones con animales.
        """
        try:
            # Si obj_in es un Pydantic model, conviértelo a dict y excluye unset
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True, exclude={"animal_ids"})
            
            # Validar claves foráneas si se proporcionan en la actualización
            if "feed_type_id" in update_data and update_data["feed_type_id"] != db_obj.feed_type_id:
                feed_type_md_q = await db.execute(select(MasterData).filter(MasterData.id == update_data["feed_type_id"]))
                if not feed_type_md_q.scalar_one_or_none():
                    raise NotFoundError(f"MasterData with ID {update_data['feed_type_id']} for new feed type not found.")
            
            if "unit_id" in update_data and update_data["unit_id"] != db_obj.unit_id:
                unit_md_q = await db.execute(select(MasterData).filter(MasterData.id == update_data["unit_id"]))
                if not unit_md_q.scalar_one_or_none():
                    raise NotFoundError(f"MasterData with ID {update_data['unit_id']} for new unit not found.")

            # Actualizar campos del evento de alimentación
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            
            # Gestionar asociaciones de animales si se proporcionan
            if obj_in.animal_ids is not None:
                current_animal_ids_q = await db.execute(
                    select(AnimalFeedingPivot.animal_id)
                    .filter(AnimalFeedingPivot.feeding_event_id == db_obj.id)
                )
                current_animal_ids = {str(id) for id in current_animal_ids_q.scalars().all()} # Convertir a set de strings para comparación

                new_animal_ids = {str(id) for id in obj_in.animal_ids}

                animals_to_add = list(new_animal_ids - current_animal_ids)
                animals_to_remove = list(current_animal_ids - new_animal_ids)

                if animals_to_add:
                    # Validar que los animales existen
                    for animal_id_to_add in animals_to_add:
                        existing_animal_q = await db.execute(select(Animal).filter(Animal.id == uuid.UUID(animal_id_to_add)))
                        if not existing_animal_q.scalar_one_or_none():
                            raise NotFoundError(f"Animal with ID {animal_id_to_add} not found. Cannot associate with feeding event.")
                    await self._add_animal_associations(db, db_obj.id, [uuid.UUID(id_str) for id_str in animals_to_add])
                
                if animals_to_remove:
                    await self._remove_animal_associations(db, db_obj.id, [uuid.UUID(id_str) for id_str in animals_to_remove])
            
            db.add(db_obj) # Marcar el objeto como modificado (aunque el super().update ya lo hace en CRUDBase)
            await db.commit()
            await db.refresh(db_obj)

            # Recargar el evento de alimentación con todas las relaciones actualizadas
            result = await db.execute(
                select(self.model)
                .options(
                    selectinload(self.model.feed_type),
                    selectinload(self.model.unit),
                    selectinload(self.model.recorded_by_user),
                    selectinload(self.model.animal_feedings).selectinload(AnimalFeedingPivot.animal)
                )
                .filter(self.model.id == db_obj.id)
            )
            return result.scalars().first()
        except Exception as e:
            await db.rollback()
            if isinstance(e, NotFoundError) or isinstance(e, AlreadyExistsError) or isinstance(e, CRUDException):
                raise e
            raise CRUDException(f"Error updating Feeding event: {str(e)}") from e


    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> Feeding: # Cambiado delete a remove
        """
        Elimina un evento de alimentación por su ID.
        Debido a `cascade="all, delete-orphan"` en la relación `animal_feedings`,
        las entradas de AnimalFeedingPivot relacionadas se eliminarán automáticamente.
        """
        db_obj = await self.get(db, id) # Primero obtenemos el objeto para asegurar que existe y para devolverlo
        if not db_obj:
            raise NotFoundError(f"Feeding event with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj # Retorna el objeto eliminado
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting Feeding event: {str(e)}") from e

# Crea una instancia de CRUDFeeding que se puede importar y usar en los routers
feeding = CRUDFeeding(Feeding)
