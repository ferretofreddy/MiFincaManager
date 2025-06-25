# app/crud/animal.py
from typing import Optional, List, Dict, Any
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
            raise AlreadyExistsError(f"Animal with tag_id '{obj_in.tag_id}' already exists.")

        try:
            # Crea el objeto Animal con los datos del esquema y el owner_user_id
            db_obj = self.model(**obj_in.model_dump(), owner_user_id=owner_user_id)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj) # Obtiene el ID, created_at, updated_at
            
            # Recarga el animal con todas sus relaciones para la respuesta completa
            result = await db.execute(
                select(Animal)
                .options(
                    selectinload(Animal.owner_user),
                    selectinload(Animal.species),
                    selectinload(Animal.breed),
                    selectinload(Animal.current_lot).selectinload(Lot.farm), # Carga anidada para lot.farm
                    selectinload(Animal.mother),
                    selectinload(Animal.father),
                    # Agrega todas las relaciones que quieras cargar por defecto al crear
                    selectinload(Animal.groups_history),
                    selectinload(Animal.locations_history),
                    selectinload(Animal.health_events_pivot),
                    selectinload(Animal.reproductive_events),
                    selectinload(Animal.sire_reproductive_events),
                    selectinload(Animal.weighings),
                    selectinload(Animal.feedings_pivot),
                    selectinload(Animal.transactions),
                    selectinload(Animal.offspring_born_events),
                )
                .filter(Animal.id == db_obj.id)
            )
            return result.scalar_one_or_none()
        except DBIntegrityError as e:
            await db.rollback()
            raise AlreadyExistsError(f"Error de integridad al crear Animal: {e}") from e
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating Animal: {str(e)}") from e

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[Animal]:
        """
        Obtiene un animal por su ID, cargando todas sus relaciones importantes.
        """
        # Las relaciones se cargan aquí para asegurar que el objeto retornado esté completo
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.owner_user),
                selectinload(self.model.species),
                selectinload(self.model.breed),
                selectinload(self.model.current_lot).selectinload(Lot.farm), # Carga anidada
                selectinload(self.model.mother),
                selectinload(self.model.father),
                selectinload(self.model.groups_history),
                selectinload(self.model.locations_history),
                selectinload(self.model.health_events_pivot),
                selectinload(self.model.reproductive_events),
                selectinload(self.model.sire_reproductive_events),
                selectinload(self.model.weighings),
                selectinload(self.model.feedings_pivot),
                selectinload(self.model.transactions),
                selectinload(self.model.offspring_born_events),
            )
            .filter(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi_by_user_and_filters(
        self, 
        db: AsyncSession, 
        user_id: uuid.UUID, 
        accessible_farm_ids: Optional[List[uuid.UUID]] = None,
        farm_id: Optional[uuid.UUID] = None, 
        lot_id: Optional[uuid.UUID] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Animal]:
        """
        Obtiene una lista de animales propiedad del usuario o de fincas a las que tiene acceso,
        opcionalmente filtrada por farm_id y/o lot_id.
        """
        query = select(self.model).options(
            selectinload(self.model.owner_user),
            selectinload(self.model.species),
            selectinload(self.model.breed),
            selectinload(self.model.current_lot).selectinload(Lot.farm)
        )

        # Criterios de filtrado basados en el acceso del usuario
        auth_filter_conditions = [
            self.model.owner_user_id == user_id
        ]
        if accessible_farm_ids:
            auth_filter_conditions.append(
                self.model.current_lot.has(Lot.farm_id.in_(accessible_farm_ids))
            )
        
        # Combina las condiciones con un OR
        query = query.filter(or_(*auth_filter_conditions))

        # Filtros adicionales si se proporcionan
        if farm_id:
            query = query.filter(self.model.current_lot.has(Lot.farm_id == farm_id))

        if lot_id:
            query = query.filter(self.model.current_lot_id == lot_id)

        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def update(self, db: AsyncSession, *, db_obj: Animal, obj_in: Union[AnimalUpdate, Dict[str, Any]]) -> Animal:
        """
        Actualiza un animal existente.
        Después de la actualización, recarga el objeto con las relaciones necesarias.
        """
        try:
            # Si obj_in es un Pydantic model, conviértelo a dict y excluye unset
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)

            # Revisa si se intenta cambiar el tag_id y si el nuevo tag_id ya existe en otro animal
            if "tag_id" in update_data and update_data["tag_id"] != db_obj.tag_id:
                existing_animal = await db.execute(
                    select(Animal).filter(
                        and_(Animal.tag_id == update_data["tag_id"], Animal.id != db_obj.id)
                    )
                )
                if existing_animal.scalar_one_or_none():
                    raise AlreadyExistsError(f"Animal with tag_id '{update_data['tag_id']}' already exists.")

            updated_animal = await super().update(db, db_obj=db_obj, obj_in=update_data)
            if updated_animal:
                # Recarga el objeto actualizado con las relaciones para la respuesta completa
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
                        selectinload(self.model.transactions),
                        selectinload(self.model.offspring_born_events),
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
