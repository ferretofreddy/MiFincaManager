# app/crud/farm.py
from typing import Optional, List, Union, Dict, Any # Añadido Union, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError as DBIntegrityError # Importa la excepción de integridad de SQLAlchemy

from app.crud.base import CRUDBase
from app.models.farm import Farm
from app.schemas.farm import FarmCreate, FarmUpdate
from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException

class CRUDFarm(CRUDBase[Farm, FarmCreate, FarmUpdate]):
    """
    Clase que implementa las operaciones CRUD específicas para el modelo Farm (Finca).
    Hereda de CRUDBase para obtener los métodos genéricos.
    """

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Farm]:
        """
        Obtiene una finca por su nombre (insensible a mayúsculas/minúsculas).

        Args:
            db (AsyncSession): La sesión asíncrona de la base de datos.
            name (str): El nombre de la finca.

        Returns:
            Optional[Farm]: El objeto Farm si se encuentra, de lo contrario, None.
        """
        query = select(self.model).where(func.lower(self.model.name) == func.lower(name))
        result = await db.execute(query)
        return result.scalars().first()

    async def get_farms_by_owner(self, db: AsyncSession, *, owner_user_id: UUID, skip: int = 0, limit: int = 100) -> List[Farm]:
        """
        Obtiene una lista de fincas propiedad de un usuario específico.

        Args:
            db (AsyncSession): La sesión asíncrona de la base de datos.
            owner_user_id (UUID): El ID del usuario propietario.
            skip (int): Número de registros a omitir (para paginación).
            limit (int): Número máximo de registros a devolver (para paginación).

        Returns:
            List[Farm]: Una lista de objetos Farm.
        """
        query = select(self.model).where(self.model.owner_user_id == owner_user_id).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: FarmCreate, owner_user_id: UUID) -> Farm:
        """
        Crea una nueva finca.
        owner_user_id es un parámetro adicional que se asigna automáticamente.
        """
        # Verificar si ya existe una finca con el mismo nombre (insensible a mayúsculas/minúsculas)
        existing_farm = await self.get_by_name(db, name=obj_in.name)
        if existing_farm:
            raise AlreadyExistsError(f"Farm with name '{obj_in.name}' already exists.")

        try:
            db_obj = self.model(**obj_in.model_dump(), owner_user_id=owner_user_id)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj) # Para cargar created_at, updated_at, y el id
            return db_obj
        except DBIntegrityError as e: # Captura errores de integridad de la DB
            await db.rollback()
            raise AlreadyExistsError(f"Error de integridad al crear Farm: {e}") from e
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating Farm: {str(e)}") from e

    async def update(self, db: AsyncSession, *, db_obj: Farm, obj_in: Union[FarmUpdate, Dict[str, Any]]) -> Farm:
        """
        Actualiza una finca existente.
        """
        try:
            # Si obj_in es un Pydantic model, conviértelo a dict y excluye unset
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)

            # Si el nombre se está actualizando, verifica unicidad
            if "name" in update_data and update_data["name"].lower() != db_obj.name.lower():
                existing_farm = await self.get_by_name(db, name=update_data["name"])
                if existing_farm and existing_farm.id != db_obj.id:
                    raise AlreadyExistsError(f"Farm with name '{update_data['name']}' already exists.")

            updated_farm = await super().update(db, db_obj=db_obj, obj_in=update_data)
            return updated_farm
        except Exception as e:
            await db.rollback()
            if isinstance(e, NotFoundError) or isinstance(e, AlreadyExistsError):
                raise e
            raise CRUDException(f"Error updating Farm: {str(e)}") from e

    async def remove(self, db: AsyncSession, *, id: UUID) -> Optional[Farm]:
        """
        Elimina una finca por su ID.
        """
        db_obj = await self.get(db, id)
        if not db_obj:
            raise NotFoundError(f"Farm with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting Farm: {str(e)}") from e

# Crea una instancia de CRUDFarm que será importada y usada en otros módulos.
farm = CRUDFarm(Farm)
