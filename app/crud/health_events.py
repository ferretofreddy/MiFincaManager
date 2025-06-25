# app/crud/health_events.py
from typing import Optional, List, Union, Dict, Any # Añadido Union, Dict, Any
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, delete # Importado delete para _remove_animal_associations
from sqlalchemy.exc import IntegrityError as DBIntegrityError # Importa la excepción de integridad de SQLAlchemy


# Importa el modelo HealthEvent y AnimalHealthEventPivot, y los esquemas
from app.models.health_event import HealthEvent
from app.models.animal import Animal # Necesario para validar animales
from app.models.master_data import MasterData # Necesario para validar MasterData
from app.models.animal_health_event_pivot import AnimalHealthEventPivot # Necesario para la carga anidada

from app.schemas.health_event import HealthEventCreate, HealthEventUpdate
from app.schemas.animal_health_event_pivot import AnimalHealthEventPivotCreate # Aunque no se use directamente, es bueno tener el contexto

# Importa la CRUDBase y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException

class CRUDHealthEvent(CRUDBase[HealthEvent, HealthEventCreate, HealthEventUpdate]):
    """
    Clase CRUD específica para el modelo HealthEvent.
    Gestiona los eventos de salud y su asociación con animales.
    """

    async def _add_animal_associations(self, db: AsyncSession, health_event_id: uuid.UUID, animal_ids: List[uuid.UUID]):
        """
        Añade asociaciones entre un evento de salud y una lista de animales.
        """
        for animal_id in animal_ids:
            # Verificar si la asociación ya existe para evitar duplicados
            existing_pivot_q = await db.execute(
                select(AnimalHealthEventPivot)
                .filter(and_(
                    AnimalHealthEventPivot.animal_id == animal_id,
                    AnimalHealthEventPivot.health_event_id == health_event_id
                ))
            )
            existing_pivot = existing_pivot_q.scalar_one_or_none()

            if not existing_pivot:
                pivot_data = AnimalHealthEventPivotCreate(
                    animal_id=animal_id,
                    health_event_id=health_event_id,
                    notes="Automáticamente asociado durante la creación del evento de salud."
                )
                db_pivot = AnimalHealthEventPivot(**pivot_data.model_dump())
                db.add(db_pivot)
        await db.flush() # Flush para que las asociaciones se creen antes de refresh

    async def _remove_animal_associations(self, db: AsyncSession, health_event_id: uuid.UUID, animal_ids_to_remove: List[uuid.UUID]):
        """
        Remueve asociaciones entre un evento de salud y una lista de animales.
        """
        await db.execute(
            delete(AnimalHealthEventPivot)
            .where(
                and_(
                    AnimalHealthEventPivot.health_event_id == health_event_id,
                    AnimalHealthEventPivot.animal_id.in_(animal_ids_to_remove)
                )
            )
        )
        await db.flush()


    async def create(self, db: AsyncSession, *, obj_in: HealthEventCreate, administered_by_user_id: uuid.UUID) -> HealthEvent:
        """
        Crea un nuevo evento de salud y asocia los animales especificados a través de la tabla pivot.
        """
        try:
            # 1. Validar product_id y unit_id como MasterData si se proporcionan
            if obj_in.product_id:
                product_md_q = await db.execute(select(MasterData).filter(MasterData.id == obj_in.product_id))
                product_md = product_md_q.scalar_one_or_none()
                if not product_md:
                    raise NotFoundError(f"MasterData with ID {obj_in.product_id} for product not found.")
                # if product_md.category != "product_category":
                #     raise CRUDException("Invalid category for product_id.")
            
            if obj_in.unit_id:
                unit_md_q = await db.execute(select(MasterData).filter(MasterData.id == obj_in.unit_id))
                unit_md = unit_md_q.scalar_one_or_none()
                if not unit_md:
                    raise NotFoundError(f"MasterData with ID {obj_in.unit_id} for unit not found.")
                # if unit_md.category != "unit_category":
                #     raise CRUDException("Invalid category for unit_id.")

            # Crear el evento de salud principal
            health_event_data = obj_in.model_dump(exclude={"animal_ids"})
            db_health_event = self.model(**health_event_data, administered_by_user_id=administered_by_user_id)
            db.add(db_health_event)
            await db.flush() # Para que db_health_event tenga un ID antes de crear pivotes

            # Crear entradas en la tabla pivot AnimalHealthEventPivot para cada animal
            if obj_in.animal_ids:
                # Validar que los animales existen
                for animal_id in obj_in.animal_ids:
                    existing_animal_q = await db.execute(select(Animal).filter(Animal.id == animal_id))
                    if not existing_animal_q.scalar_one_or_none():
                        raise NotFoundError(f"Animal with ID {animal_id} not found. Cannot associate with health event.")
                
                await self._add_animal_associations(db, db_health_event.id, obj_in.animal_ids)

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
            return result.scalars().first()
        except DBIntegrityError as e:
            await db.rollback()
            raise AlreadyExistsError(f"Error de integridad al crear HealthEvent: {e}") from e
        except Exception as e:
            await db.rollback()
            if isinstance(e, NotFoundError) or isinstance(e, AlreadyExistsError):
                raise e
            raise CRUDException(f"Error creating HealthEvent: {str(e)}") from e

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[HealthEvent]: # Cambiado health_event_id a id
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
            .filter(self.model.id == id) # Cambiado health_event_id a id
        )
        return result.scalars().first()

    async def get_multi_by_animal_id(self, db: AsyncSession, animal_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[HealthEvent]:
        """
        Obtiene todos los eventos de salud asociados a un animal específico.
        """
        # Unimos a la tabla de pivote para filtrar por animal_id
        result = await db.execute(
            select(self.model)
            .join(AnimalHealthEventPivot)
            .filter(AnimalHealthEventPivot.animal_id == animal_id)
            .options(
                selectinload(self.model.animals_affected).selectinload(AnimalHealthEventPivot.animal),
                selectinload(self.model.product),
                selectinload(self.model.unit),
                selectinload(self.model.administered_by_user)
            )
            .order_by(self.model.event_date.desc()) # Ordenar por fecha de evento descendente
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().unique().all() # .unique() para evitar duplicados si un animal está en varios pivotes


    async def update(self, db: AsyncSession, *, db_obj: HealthEvent, obj_in: Union[HealthEventUpdate, Dict[str, Any]]) -> HealthEvent: # Añadido Union, Dict, Any
        """
        Actualiza un evento de salud existente y sus asociaciones con animales.
        """
        try:
            # Si obj_in es un Pydantic model, conviértelo a dict y excluye unset
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True, exclude={"animal_ids"})

            # Validar claves foráneas si se proporcionan en la actualización
            if "product_id" in update_data and update_data["product_id"] != db_obj.product_id:
                product_md_q = await db.execute(select(MasterData).filter(MasterData.id == update_data["product_id"]))
                if not product_md_q.scalar_one_or_none():
                    raise NotFoundError(f"MasterData with ID {update_data['product_id']} for new product not found.")
            
            if "unit_id" in update_data and update_data["unit_id"] != db_obj.unit_id:
                unit_md_q = await db.execute(select(MasterData).filter(MasterData.id == update_data["unit_id"]))
                if not unit_md_q.scalar_one_or_none():
                    raise NotFoundError(f"MasterData with ID {update_data['unit_id']} for new unit not found.")

            # Actualizar campos del evento de salud
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            
            # Gestionar asociaciones de animales si se proporcionan
            if obj_in.animal_ids is not None:
                current_animal_ids_q = await db.execute(
                    select(AnimalHealthEventPivot.animal_id)
                    .filter(AnimalHealthEventPivot.health_event_id == db_obj.id)
                )
                current_animal_ids = {str(id) for id in current_animal_ids_q.scalars().all()}

                new_animal_ids = {str(id) for id in obj_in.animal_ids}

                animals_to_add = list(new_animal_ids - current_animal_ids)
                animals_to_remove = list(current_animal_ids - new_animal_ids)

                if animals_to_add:
                    for animal_id_to_add in animals_to_add:
                        existing_animal_q = await db.execute(select(Animal).filter(Animal.id == uuid.UUID(animal_id_to_add)))
                        if not existing_animal_q.scalar_one_or_none():
                            raise NotFoundError(f"Animal with ID {animal_id_to_add} not found. Cannot associate with health event.")
                    await self._add_animal_associations(db, db_obj.id, [uuid.UUID(id_str) for id_str in animals_to_add])
                
                if animals_to_remove:
                    await self._remove_animal_associations(db, db_obj.id, [uuid.UUID(id_str) for id_str in animals_to_remove])
            
            db.add(db_obj) # Marcar el objeto como modificado
            await db.commit()
            await db.refresh(db_obj)

            # Recargar el evento de salud con todas las relaciones actualizadas
            result = await db.execute(
                select(self.model)
                .options(
                    selectinload(self.model.animals_affected).selectinload(AnimalHealthEventPivot.animal),
                    selectinload(self.model.product),
                    selectinload(self.model.unit),
                    selectinload(self.model.administered_by_user)
                )
                .filter(self.model.id == db_obj.id)
            )
            return result.scalars().first()
        except Exception as e:
            await db.rollback()
            if isinstance(e, NotFoundError) or isinstance(e, AlreadyExistsError) or isinstance(e, CRUDException):
                raise e
            raise CRUDException(f"Error updating HealthEvent: {str(e)}") from e

    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> HealthEvent: # Cambiado delete a remove
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
