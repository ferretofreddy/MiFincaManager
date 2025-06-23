# app/crud/batches.py
from typing import Optional, List
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import and_

# Importa el modelo Batch y los esquemas
from app.models.batch import Batch
from app.models.animal import Animal # Necesario para validar animales
from app.models.master_data import MasterData # Necesario para validar MasterData
from app.models.farm import Farm # Necesario para validar Farm
from app.models.animal_batch_pivot import AnimalBatchPivot # Necesario para gestionar pivotes

from app.schemas.batch import BatchCreate, BatchUpdate
from app.schemas.animal_batch_pivot import AnimalBatchPivotCreate

# Importa la CRUDBase y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, CRUDException

class CRUDBatch(CRUDBase[Batch, BatchCreate, BatchUpdate]):
    """
    Clase CRUD específica para el modelo Batch.
    Gestiona los lotes de animales, incluyendo la asociación con animales.
    """

    async def _add_animal_associations(self, db: AsyncSession, batch_event_id: uuid.UUID, animal_ids: List[uuid.UUID]):
        """
        Añade asociaciones entre un lote y una lista de animales.
        """
        for animal_id in animal_ids:
            # Verificar si la asociación ya existe para evitar duplicados
            existing_pivot_q = await db.execute(
                select(AnimalBatchPivot)
                .filter(and_(
                    AnimalBatchPivot.animal_id == animal_id,
                    AnimalBatchPivot.batch_event_id == batch_event_id
                ))
            )
            existing_pivot = existing_pivot_q.scalar_one_or_none()

            if not existing_pivot:
                pivot_data = AnimalBatchPivotCreate(
                    animal_id=animal_id,
                    batch_event_id=batch_event_id,
                    assigned_date=datetime.utcnow(),
                    notes="Automáticamente asociado durante la creación/actualización del lote."
                )
                db_pivot = AnimalBatchPivot(**pivot_data.model_dump())
                db.add(db_pivot)
        await db.flush() # Flush para que las asociaciones se creen antes de refresh

    async def _remove_animal_associations(self, db: AsyncSession, batch_event_id: uuid.UUID, animal_ids_to_remove: List[uuid.UUID]):
        """
        Remueve asociaciones entre un lote y una lista de animales.
        """
        for animal_id in animal_ids_to_remove:
            await db.execute(
                select(AnimalBatchPivot)
                .filter(and_(
                    AnimalBatchPivot.animal_id == animal_id,
                    AnimalBatchPivot.batch_event_id == batch_event_id
                ))
                .delete()
            )
        await db.flush()


    async def create(self, db: AsyncSession, *, obj_in: BatchCreate, created_by_user_id: uuid.UUID) -> Batch:
        """
        Crea un nuevo lote y asocia los animales especificados.
        """
        try:
            # 1. Validar batch_type_id como MasterData
            batch_type_md = await db.execute(select(MasterData).filter(MasterData.id == obj_in.batch_type_id))
            batch_type_md = batch_type_md.scalar_one_or_none()
            if not batch_type_md:
                raise CRUDException(f"MasterData with ID {obj_in.batch_type_id} for batch type not found.")
            # Puedes añadir una validación de categoría si 'batch_type' debe ser de una categoría específica.

            # 2. Validar farm_id
            farm = await db.execute(select(Farm).filter(Farm.id == obj_in.farm_id))
            if not farm.scalar_one_or_none():
                raise NotFoundError(f"Farm with ID {obj_in.farm_id} not found.")

            # Crear el lote principal
            batch_data = obj_in.model_dump(exclude={"animal_ids"})
            db_batch = self.model(**batch_data, created_by_user_id=created_by_user_id)
            db.add(db_batch)
            await db.flush() # Flush para obtener el ID del nuevo lote

            # 3. Asociar animales si se proporcionan
            if obj_in.animal_ids:
                # Validar que los animales existen
                for animal_id in obj_in.animal_ids:
                    existing_animal = await db.execute(select(Animal).filter(Animal.id == animal_id))
                    if not existing_animal.scalar_one_or_none():
                        raise NotFoundError(f"Animal with ID {animal_id} not found. Cannot associate with batch.")
                
                await self._add_animal_associations(db, db_batch.id, obj_in.animal_ids)
            
            await db.commit()
            await db.refresh(db_batch) # Refresh final después de todas las operaciones

            # Recargar el lote con todas las relaciones, incluyendo los pivotes
            result = await db.execute(
                select(Batch)
                .options(
                    selectinload(Batch.batch_type),
                    selectinload(Batch.farm),
                    selectinload(Batch.created_by_user),
                    selectinload(Batch.animal_batches).selectinload(AnimalBatchPivot.animal) # Cargar también los animales asociados
                )
                .filter(Batch.id == db_batch.id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            if isinstance(e, NotFoundError) or isinstance(e, CRUDException):
                raise e
            raise CRUDException(f"Error creating Batch: {str(e)}") from e

    async def get(self, db: AsyncSession, batch_id: uuid.UUID) -> Optional[Batch]:
        """
        Obtiene un lote por su ID, cargando las relaciones.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.batch_type),
                selectinload(self.model.farm),
                selectinload(self.model.created_by_user),
                selectinload(self.model.animal_batches).selectinload(AnimalBatchPivot.animal)
            )
            .filter(self.model.id == batch_id)
        )
        return result.scalar_one_or_none()

    async def get_multi_by_farm_id(self, db: AsyncSession, farm_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Batch]:
        """
        Obtiene todos los lotes asociados a una granja específica.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.batch_type),
                selectinload(self.model.farm),
                selectinload(self.model.created_by_user),
                selectinload(self.model.animal_batches).selectinload(AnimalBatchPivot.animal)
            )
            .filter(self.model.farm_id == farm_id)
            .order_by(self.model.start_date.desc()) # Ordenar por fecha de inicio descendente
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().unique().all()

    async def get_multi_by_animal_id(self, db: AsyncSession, animal_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Batch]:
        """
        Obtiene todos los lotes en los que un animal específico ha participado.
        """
        # Unimos a la tabla de pivote para filtrar por animal_id
        result = await db.execute(
            select(self.model)
            .join(AnimalBatchPivot)
            .filter(AnimalBatchPivot.animal_id == animal_id)
            .options(
                selectinload(self.model.batch_type),
                selectinload(self.model.farm),
                selectinload(self.model.created_by_user),
                selectinload(self.model.animal_batches).selectinload(AnimalBatchPivot.animal)
            )
            .order_by(self.model.start_date.desc()) # Ordenar por fecha de inicio descendente
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().unique().all()


    async def update(self, db: AsyncSession, *, db_obj: Batch, obj_in: BatchUpdate) -> Batch:
        """
        Actualiza un lote existente y sus asociaciones con animales.
        """
        try:
            # Validar claves foráneas si se proporcionan en la actualización
            if obj_in.batch_type_id is not None:
                batch_type_md = await db.execute(select(MasterData).filter(MasterData.id == obj_in.batch_type_id))
                if not batch_type_md.scalar_one_or_none():
                    raise CRUDException(f"MasterData with ID {obj_in.batch_type_id} for batch type not found.")
            
            if obj_in.farm_id is not None:
                farm = await db.execute(select(Farm).filter(Farm.id == obj_in.farm_id))
                if not farm.scalar_one_or_none():
                    raise NotFoundError(f"Farm with ID {obj_in.farm_id} not found.")

            # Actualizar campos del lote
            update_data = obj_in.model_dump(exclude_unset=True, exclude={"animal_ids"})
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            
            # Gestionar asociaciones de animales si se proporcionan
            if obj_in.animal_ids is not None:
                current_animal_ids_q = await db.execute(
                    select(AnimalBatchPivot.animal_id)
                    .filter(AnimalBatchPivot.batch_event_id == db_obj.id)
                )
                current_animal_ids = {str(id) for id in current_animal_ids_q.scalars().all()} # Convertir a set de strings para comparación

                new_animal_ids = {str(id) for id in obj_in.animal_ids}

                animals_to_add = list(new_animal_ids - current_animal_ids)
                animals_to_remove = list(current_animal_ids - new_animal_ids)

                if animals_to_add:
                    # Validar que los animales existen
                    for animal_id_to_add in animals_to_add:
                        existing_animal = await db.execute(select(Animal).filter(Animal.id == uuid.UUID(animal_id_to_add)))
                        if not existing_animal.scalar_one_or_none():
                            raise NotFoundError(f"Animal with ID {animal_id_to_add} not found. Cannot associate with batch.")
                    await self._add_animal_associations(db, db_obj.id, [uuid.UUID(id_str) for id_str in animals_to_add])
                
                if animals_to_remove:
                    await self._remove_animal_associations(db, db_obj.id, [uuid.UUID(id_str) for id_str in animals_to_remove])
            
            db.add(db_obj) # Marcar el objeto como modificado
            await db.commit()
            await db.refresh(db_obj)

            # Recargar el lote con todas las relaciones actualizadas
            result = await db.execute(
                select(self.model)
                .options(
                    selectinload(self.model.batch_type),
                    selectinload(self.model.farm),
                    selectinload(self.model.created_by_user),
                    selectinload(self.model.animal_batches).selectinload(AnimalBatchPivot.animal)
                )
                .filter(self.model.id == db_obj.id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            if isinstance(e, NotFoundError) or isinstance(e, CRUDException):
                raise e
            raise CRUDException(f"Error updating Batch: {str(e)}") from e


    async def delete(self, db: AsyncSession, *, id: uuid.UUID) -> Batch:
        """
        Elimina un lote por su ID.
        Debido a `cascade="all, delete-orphan"` en la relación `animal_batches`,
        las entradas de AnimalBatchPivot relacionadas se eliminarán automáticamente.
        """
        db_obj = await self.get(db, id) # Primero obtenemos el objeto para asegurar que existe y para devolverlo
        if not db_obj:
            raise NotFoundError(f"Batch with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj # Retorna el objeto eliminado
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting Batch: {str(e)}") from e

# Crea una instancia de CRUDBatch que se puede importar y usar en los routers
batch = CRUDBatch(Batch)
