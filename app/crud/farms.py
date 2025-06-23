# app/crud/farms.py
from typing import Optional, List
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

# Importa el modelo Farm y los esquemas de farm
from app.models.farm import Farm
from app.schemas.farm import FarmCreate, FarmUpdate

# Importa la CRUDBase y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException

class CRUDFarm(CRUDBase[Farm, FarmCreate, FarmUpdate]):
    """
    Clase CRUD específica para el modelo Farm.
    Hereda la mayoría de las operaciones de CRUDBase.
    Implementa métodos específicos para Farm que requieren lógica adicional
    (ej. carga de relaciones).
    """

    async def create(self, db: AsyncSession, *, obj_in: FarmCreate, owner_user_id: uuid.UUID) -> Farm:
        """
        Crea una nueva finca.
        owner_user_id es un parámetro adicional que no está en FarmCreate.
        """
        # Verifica si ya existe una finca con el mismo nombre para este usuario (o a nivel global si es único)
        # Esto es un ejemplo, ajusta la lógica de unicidad según tu negocio
        # Si Farm.name debe ser único por owner_user_id:
        existing_farm = await db.execute(
            select(Farm).filter(Farm.name == obj_in.name, Farm.owner_user_id == owner_user_id)
        )
        if existing_farm.scalar_one_or_none():
            raise AlreadyExistsError(f"Farm with name '{obj_in.name}' already exists for this user.")

        try:
            # Combina los datos del esquema de entrada con el owner_user_id
            db_obj = self.model(**obj_in.model_dump(), owner_user_id=owner_user_id)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj) # Obtiene el ID, created_at, updated_at
            
            # Recarga la finca con la relación owner_user para la respuesta
            # Usa selectinload para cargar la relación 'owner_user'
            result = await db.execute(
                select(Farm)
                .options(selectinload(Farm.owner_user))
                .filter(Farm.id == db_obj.id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating Farm: {str(e)}") from e


    async def get(self, db: AsyncSession, farm_id: uuid.UUID) -> Optional[Farm]:
        """
        Obtiene una finca por su ID, cargando la relación con el usuario propietario.
        """
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.owner_user)) # Carga la relación 'owner_user'
            .filter(self.model.id == farm_id)
        )
        return result.scalar_one_or_none()

    async def get_multi_by_owner(self, db: AsyncSession, owner_user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Farm]:
        """
        Obtiene una lista de fincas por el ID del usuario propietario.
        """
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.owner_user)) # Carga la relación 'owner_user'
            .filter(self.model.owner_user_id == owner_user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, db: AsyncSession, *, db_obj: Farm, obj_in: FarmUpdate) -> Farm:
        """
        Actualiza una finca existente.
        Después de la actualización, recarga el objeto con las relaciones necesarias.
        """
        updated_farm = await super().update(db, db_obj=db_obj, obj_in=obj_in)
        if updated_farm:
            # Recarga el objeto actualizado con las relaciones si es necesario para la respuesta
            result = await db.execute(
                select(self.model)
                .options(selectinload(self.model.owner_user))
                .filter(self.model.id == updated_farm.id)
            )
            return result.scalar_one_or_none()
        return updated_farm

# Crea una instancia de CRUDFarm que se puede importar y usar en los routers
farm = CRUDFarm(Farm)
