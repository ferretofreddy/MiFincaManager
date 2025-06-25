# app/crud/animal.py
from typing import Optional, List, Dict, Any
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import or_, and_, func # Importa 'or_', 'and_', y 'func' para combinaciones de filtros y funciones SQL

# Importa los modelos necesarios
from app.models.animal import Animal
from app.models.lot import Lot # ¡IMPORTADO! Necesario para Lot.farm
from app.models.farm import Farm # ¡IMPORTADO! Necesario para la comprobación del dueño de la finca
from app.schemas.animal import AnimalCreate, AnimalUpdate

# Importa la CRUDBase y las excepciones
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
                )
                .filter(Animal.id == db_obj.id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating Animal: {str(e)}") from e

    async def get(self, db: AsyncSession, animal_id: uuid.UUID) -> Optional[Animal]:
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
            .filter(self.model.id == animal_id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi_by_user_and_filters(
        self, 
        db: AsyncSession, 
        user_id: uuid.UUID, 
        accessible_farm_ids: List[uuid.UUID],
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
            selectinload(self.model.current_lot).selectinload(Lot.farm) # Carga anidada para lot.farm
        )

        # Criterios de filtrado basados en el acceso del usuario
        auth_filter_conditions = [
            self.model.owner_user_id == user_id # Animales propiedad del usuario
        ]
        if accessible_farm_ids:
            # Animales en fincas a las que el usuario tiene acceso
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


    async def update(self, db: AsyncSession, *, db_obj: Animal, obj_in: AnimalUpdate) -> Animal:
        """
        Actualiza un animal existente.
        Después de la actualización, recarga el objeto con las relaciones necesarias.
        """
        updated_animal = await super().update(db, db_obj=db_obj, obj_in=obj_in)
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
                    selectinload(self.model.groups_history), # Asegurarse de recargar todas las relaciones
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
            return result.scalars().first() # Usar first() en lugar de scalar_one_or_none() ya que sabemos que existe
        return updated_animal

# Crea una instancia de CRUDAnimal que se puede importar y usar en los routers
animal = CRUDAnimal(Animal)

