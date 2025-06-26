# app/crud/animal.py
from typing import Optional, List, Dict, Any, Union
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import or_, and_, func
from sqlalchemy.exc import IntegrityError as DBIntegrityError # Importa la excepción de integridad de SQLAlchemy

from app.models.animal import Animal
from app.models.lot import Lot
from app.models.farm import Farm
from app.schemas.animal import AnimalCreate, AnimalUpdate

from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException

class CRUDAnimal(CRUDBase[Animal, AnimalCreate, AnimalUpdate]):
    """
    Clase CRUD específica para el modelo Animal.
    Hereda la mayoría de las operaciones de CRUDBase.
    Implementa métodos específicos para Animal que requieren lógica adicional
    (ej. carga de relaciones, filtros complejos).
    """
    async def create(self, db: AsyncSession, *, obj_in: AnimalCreate, owner_user_id: uuid.UUID) -> Animal:
        """
        Crea un nuevo animal.
        owner_user_id es un parámetro adicional.
        Verifica la unicidad del tag_id.
        """
        # Verifica si ya existe un animal con el mismo tag_id
        existing_animal = await db.execute(
            select(Animal).filter(Animal.tag_id == obj_in.tag_id)
        )
        if existing_animal.scalar_one_or_none():
            raise AlreadyExistsError(f"Animal with tag ID '{obj_in.tag_id}' already exists.")
        
        # Validar current_lot_id si se proporciona
        if obj_in.current_lot_id:
            lot_exists = await db.execute(select(Lot).filter(Lot.id == obj_in.current_lot_id))
            if not lot_exists.scalar_one_or_none():
                raise NotFoundError(f"Lot with ID {obj_in.current_lot_id} not found.")

        # Validar species_id y breed_id (MasterData)
        if obj_in.species_id:
            species_md = await db.execute(select(models.MasterData).filter(models.MasterData.id == obj_in.species_id))
            if not species_md.scalar_one_or_none():
                raise NotFoundError(f"Species MasterData with ID {obj_in.species_id} not found.")
        if obj_in.breed_id:
            breed_md = await db.execute(select(models.MasterData).filter(models.MasterData.id == obj_in.breed_id))
            if not breed_md.scalar_one_or_none():
                raise NotFoundError(f"Breed MasterData with ID {obj_in.breed_id} not found.")
        
        # Validar mother_animal_id y father_animal_id
        if obj_in.mother_animal_id:
            mother_exists = await db.execute(select(Animal).filter(Animal.id == obj_in.mother_animal_id))
            if not mother_exists.scalar_one_or_none():
                raise NotFoundError(f"Mother animal with ID {obj_in.mother_animal_id} not found.")
        if obj_in.father_animal_id:
            father_exists = await db.execute(select(Animal).filter(Animal.id == obj_in.father_animal_id))
            if not father_exists.scalar_one_or_none():
                raise NotFoundError(f"Father animal with ID {obj_in.father_animal_id} not found.")

        try:
            db_animal = self.model(**obj_in.model_dump(), owner_user_id=owner_user_id)
            db.add(db_animal)
            await db.commit()
            await db.refresh(db_animal)

            # Recargar el animal con las relaciones para la respuesta completa
            result = await db.execute(
                select(self.model)
                .options(
                    selectinload(self.model.owner_user),
                    selectinload(self.model.species),
                    selectinload(self.model.breed),
                    selectinload(self.model.current_lot).selectinload(Lot.farm),
                    selectinload(self.model.mother),
                    selectinload(self.model.father),
                    selectinload(self.model.groups_history),
                    selectinload(self.model.locations_history),
                    selectinload(self.model.health_events_pivot),
                    selectinload(self.model.reproductive_events),
                    selectinload(self.model.sire_reproductive_events),
                    selectinload(self.model.weighings),
                    selectinload(self.model.feedings_pivot),
                    # REMOVER ESTA LÍNEA: selectinload(self.model.transactions),
                    selectinload(self.model.offspring_born_events),
                    selectinload(self.model.batches_pivot) # Asegúrate de que esto se añadió previamente
                )
                .filter(self.model.id == db_animal.id)
            )
            return result.scalars().first()
        except DBIntegrityError as e:
            await db.rollback()
            raise AlreadyExistsError(f"Error de integridad al crear Animal: {e}") from e
        except Exception as e:
            await db.rollback()
            if isinstance(e, (NotFoundError, AlreadyExistsError)):
                raise e
            raise CRUDException(f"Error creating Animal: {str(e)}") from e

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[Animal]:
        """
        Obtiene un animal por su ID, cargando sus relaciones.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.owner_user),
                selectinload(self.model.species),
                selectinload(self.model.breed),
                selectinload(self.model.current_lot).selectinload(Lot.farm),
                selectinload(self.model.mother),
                selectinload(self.model.father),
                selectinload(self.model.groups_history),
                selectinload(self.model.locations_history),
                selectinload(self.model.health_events_pivot),
                selectinload(self.model.reproductive_events),
                selectinload(self.model.sire_reproductive_events),
                selectinload(self.model.weighings),
                selectinload(self.model.feedings_pivot),
                # REMOVER ESTA LÍNEA: selectinload(self.model.transactions),
                selectinload(self.model.offspring_born_events),
                selectinload(self.model.batches_pivot)
            )
            .filter(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Animal]:
        """
        Obtiene múltiples animales, cargando sus relaciones.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.owner_user),
                selectinload(self.model.species),
                selectinload(self.model.breed),
                selectinload(self.model.current_lot),
                selectinload(self.model.mother),
                selectinload(self.model.father)
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_animals_by_owner(self, db: AsyncSession, owner_user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Animal]:
        """
        Obtiene animales por el ID de su propietario.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.owner_user),
                selectinload(self.model.species),
                selectinload(self.model.breed),
                selectinload(self.model.current_lot)
            )
            .filter(self.model.owner_user_id == owner_user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_animals_by_lot(self, db: AsyncSession, lot_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Animal]:
        """
        Obtiene animales por el ID del lote actual al que pertenecen.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.owner_user),
                selectinload(self.model.species),
                selectinload(self.model.breed),
                selectinload(self.model.current_lot)
            )
            .filter(self.model.current_lot_id == lot_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_tag_id(self, db: AsyncSession, tag_id: str) -> Optional[Animal]:
        """
        Obtiene un animal por su tag_id (sensible a mayúsculas/minúsculas).
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.owner_user),
                selectinload(self.model.species),
                selectinload(self.model.breed),
                selectinload(self.model.current_lot)
            )
            .filter(self.model.tag_id == tag_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[List[Animal]]:
        """
        Obtiene animales por su nombre (insensible a mayúsculas/minúsculas).
        Retorna una lista ya que los nombres pueden no ser únicos.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.owner_user),
                selectinload(self.model.species),
                selectinload(self.model.breed),
                selectinload(self.model.current_lot)
            )
            .filter(func.lower(self.model.name) == func.lower(name))
        )
        return result.scalars().all()

    async def update(self, db: AsyncSession, *, db_obj: Animal, obj_in: Union[AnimalUpdate, Dict[str, Any]]) -> Animal:
        """
        Actualiza un animal existente.
        """
        try:
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)

            # Validaciones si los IDs de MasterData o Lot cambian
            if "species_id" in update_data and update_data["species_id"] != db_obj.species_id:
                species_md = await db.execute(select(models.MasterData).filter(models.MasterData.id == update_data["species_id"]))
                if not species_md.scalar_one_or_none():
                    raise NotFoundError(f"Species MasterData with ID {update_data['species_id']} not found.")
            
            if "breed_id" in update_data and update_data["breed_id"] != db_obj.breed_id:
                breed_md = await db.execute(select(models.MasterData).filter(models.MasterData.id == update_data["breed_id"]))
                if not breed_md.scalar_one_or_none():
                    raise NotFoundError(f"Breed MasterData with ID {update_data['breed_id']} not found.")

            if "current_lot_id" in update_data and update_data["current_lot_id"] != db_obj.current_lot_id:
                lot_exists = await db.execute(select(Lot).filter(Lot.id == update_data["current_lot_id"]))
                if not lot_exists.scalar_one_or_none():
                    raise NotFoundError(f"Lot with ID {update_data['current_lot_id']} not found.")

            # Validar mother_animal_id y father_animal_id si cambian
            if "mother_animal_id" in update_data and update_data["mother_animal_id"] != db_obj.mother_animal_id:
                mother_exists = await db.execute(select(Animal).filter(Animal.id == update_data["mother_animal_id"]))
                if not mother_exists.scalar_one_or_none():
                    raise NotFoundError(f"Mother animal with ID {update_data['mother_animal_id']} not found.")
            if "father_animal_id" in update_data and update_data["father_animal_id"] != db_obj.father_animal_id:
                father_exists = await db.execute(select(Animal).filter(Animal.id == update_data["father_animal_id"]))
                if not father_exists.scalar_one_or_none():
                    raise NotFoundError(f"Father animal with ID {update_data['father_animal_id']} not found.")

            # Si el tag_id se actualiza, verifica unicidad
            if "tag_id" in update_data and update_data["tag_id"] != db_obj.tag_id:
                existing_animal_with_tag = await self.get_by_tag_id(db, tag_id=update_data["tag_id"])
                if existing_animal_with_tag and existing_animal_with_tag.id != db_obj.id:
                    raise AlreadyExistsError(f"Animal with tag ID '{update_data['tag_id']}' already exists.")

            updated_animal = await super().update(db, db_obj=db_obj, obj_in=update_data)
            if updated_animal:
                # Recargar el animal actualizado con las relaciones para la respuesta completa
                result = await db.execute(
                    select(self.model)
                    .options(
                        selectinload(self.model.owner_user),
                        selectinload(self.model.species),
                        selectinload(self.model.breed),
                        selectinload(self.model.current_lot).selectinload(Lot.farm),
                        selectinload(self.model.mother),
                        selectinload(self.model.father),
                        selectinload(self.model.groups_history),
                        selectinload(self.model.locations_history),
                        selectinload(self.model.health_events_pivot),
                        selectinload(self.model.reproductive_events),
                        selectinload(self.model.sire_reproductive_events),
                        selectinload(self.model.weighings),
                        selectinload(self.model.feedings_pivot),
                        # REMOVER ESTA LÍNEA: selectinload(self.model.transactions),
                        selectinload(self.model.offspring_born_events),
                        selectinload(self.model.batches_pivot)
                    )
                    .filter(self.model.id == updated_animal.id)
                )
                return result.scalars().first()
            return updated_animal
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error updating Animal: {str(e)}") from e

    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[Animal]:
        """
        Elimina un animal por su ID.
        """
        db_obj = await self.get(db, id) # Primero obtenemos el objeto para asegurar que existe y para devolverlo
        if not db_obj:
            raise NotFoundError(f"Animal with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj # Retorna el objeto eliminado
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting Animal: {str(e)}") from e


animal = CRUDAnimal(Animal)
