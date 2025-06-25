# app/crud/user_farm_access.py
from typing import List, Optional, Union, Dict, Any # Añadido Union, Dict, Any
import uuid

# Importa AsyncSession para operaciones asíncronas
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload # Para cargar relaciones
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError as DBIntegrityError # Importa la excepción de integridad de SQLAlchemy


from app.crud.base import CRUDBase
from app.models.user_farm_access import UserFarmAccess # Importa el modelo ORM
from app.models.user import User # Importado para validación
from app.models.farm import Farm # Importado para validación
from app.schemas.user_farm_access import UserFarmAccessCreate, UserFarmAccessUpdate # Importa los esquemas Pydantic
from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException

class CRUDUserFarmAccess(CRUDBase[UserFarmAccess, UserFarmAccessCreate, UserFarmAccessUpdate]):
    """
    Clase que implementa las operaciones CRUD para el modelo UserFarmAccess.
    Hereda de CRUDBase para obtener funcionalidades básicas.
    """

    async def get_by_user_and_farm(
        self, db: AsyncSession, *, user_id: uuid.UUID, farm_id: uuid.UUID
    ) -> Optional[UserFarmAccess]:
        """
        Obtiene un registro de UserFarmAccess por user_id y farm_id, cargando relaciones.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.user), # Carga relaciones si son útiles
                selectinload(self.model.farm)
            )
            .filter(
                self.model.user_id == user_id,
                self.model.farm_id == farm_id
            )
        )
        return result.scalar_one_or_none()

    async def get_user_farm_accesses_by_user(
        self, db: AsyncSession, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[UserFarmAccess]:
        """
        Obtiene todos los registros de acceso de finca para un usuario específico.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.user),
                selectinload(self.model.farm)
            )
            .filter(self.model.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_farm_user_accesses(
        self, db: AsyncSession, *, farm_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[UserFarmAccess]:
        """
        Obtiene todos los registros de acceso de los usuarios a una granja específica.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.user),
                selectinload(self.model.farm)
            )
            .filter(self.model.farm_id == farm_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create_access(self, db: AsyncSession, *, obj_in: UserFarmAccessCreate, assigned_by_user_id: uuid.UUID) -> UserFarmAccess:
        """
        Crea un nuevo registro de acceso de usuario a finca.
        """
        # Validar que el user_id y farm_id existen
        user_exists_q = await db.execute(select(User).filter(User.id == obj_in.user_id))
        if not user_exists_q.scalar_one_or_none():
            raise NotFoundError(f"User with ID {obj_in.user_id} not found.")

        farm_exists_q = await db.execute(select(Farm).filter(Farm.id == obj_in.farm_id))
        if not farm_exists_q.scalar_one_or_none():
            raise NotFoundError(f"Farm with ID {obj_in.farm_id} not found.")

        existing_access = await self.get_by_user_and_farm(db, user_id=obj_in.user_id, farm_id=obj_in.farm_id)
        if existing_access:
            raise AlreadyExistsError(f"User {obj_in.user_id} already has access to farm {obj_in.farm_id}.")
        
        try:
            db_obj = self.model(**obj_in.model_dump(), assigned_by_user_id=assigned_by_user_id)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            # Recargar con relaciones para la respuesta
            return await self.get(db, db_obj.id) # Usar el método get que ya carga relaciones
        except DBIntegrityError as e:
            await db.rollback()
            raise AlreadyExistsError(f"Error de integridad al crear UserFarmAccess: {e}") from e
        except Exception as e:
            await db.rollback()
            if isinstance(e, (NotFoundError, AlreadyExistsError)):
                raise e
            raise CRUDException(f"Error creating UserFarmAccess: {str(e)}") from e

    async def update(self, db: AsyncSession, *, db_obj: UserFarmAccess, obj_in: Union[UserFarmAccessUpdate, Dict[str, Any]]) -> UserFarmAccess:
        """
        Actualiza un registro de UserFarmAccess existente.
        """
        try:
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)

            # No permitir cambiar user_id o farm_id en una actualización
            if "user_id" in update_data and update_data["user_id"] != db_obj.user_id:
                raise CRUDException("Changing 'user_id' for an existing access record is not allowed. Create a new one.")
            if "farm_id" in update_data and update_data["farm_id"] != db_obj.farm_id:
                raise CRUDException("Changing 'farm_id' for an existing access record is not allowed. Create a new one.")

            updated_access = await super().update(db, db_obj=db_obj, obj_in=update_data)
            if updated_access:
                return await self.get(db, updated_access.id)
            return updated_access
        except Exception as e:
            await db.rollback()
            if isinstance(e, (NotFoundError, AlreadyExistsError, CRUDException)):
                raise e
            raise CRUDException(f"Error updating UserFarmAccess: {str(e)}") from e


    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[UserFarmAccess]:
        """
        Elimina un registro de UserFarmAccess por su ID.
        """
        db_obj = await self.get(db, id)
        if not db_obj:
            raise NotFoundError(f"UserFarmAccess with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting UserFarmAccess: {str(e)}") from e

user_farm_access = CRUDUserFarmAccess(UserFarmAccess)
