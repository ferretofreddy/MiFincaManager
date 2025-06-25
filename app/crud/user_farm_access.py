# app/crud/user_farm_access.py
from typing import List, Optional
import uuid

# Importa AsyncSession para operaciones asíncronas
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload # Para cargar relaciones

from app.crud.base import CRUDBase
from app.models.user_farm_access import UserFarmAccess # Importa el modelo ORM
from app.schemas.user_farm_access import UserFarmAccessCreate, UserFarmAccessUpdate # Importa los esquemas Pydantic

class CRUDUserFarmAccess(CRUDBase[UserFarmAccess, UserFarmAccessCreate, UserFarmAccessUpdate]):
    """
    Clase que implementa las operaciones CRUD para el modelo UserFarmAccess.
    Hereda de CRUDBase para obtener funcionalidades básicas.
    """

    async def get_by_user_and_farm(
        self, db: AsyncSession, *, user_id: uuid.UUID, farm_id: uuid.UUID
    ) -> Optional[UserFarmAccess]:
        """
        Obtiene un registro de UserFarmAccess por user_id y farm_id.
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
        return result.scalars().first()

    async def get_user_farm_accesses(
        self, db: AsyncSession, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[UserFarmAccess]:
        """
        Obtiene todos los registros de acceso de granjas para un usuario específico.
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

    # Considera añadir un método de creación específico si hay validaciones
    # adicionales más allá de CRUDBase.create()
    async def create_access(self, db: AsyncSession, *, obj_in: UserFarmAccessCreate) -> UserFarmAccess:
        """
        Crea un nuevo registro de acceso de usuario a finca.
        """
        # Puedes añadir validaciones de existencia aquí si es necesario
        existing_access = await self.get_by_user_and_farm(db, user_id=obj_in.user_id, farm_id=obj_in.farm_id)
        if existing_access:
            raise AlreadyExistsError(f"User {obj_in.user_id} already has access to farm {obj_in.farm_id}.")
        
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        # Recargar con relaciones para la respuesta
        return await self.get_by_user_and_farm(db, user_id=db_obj.user_id, farm_id=db_obj.farm_id)


# Crea una instancia de CRUDUserFarmAccess que se puede importar y usar en los routers
user_farm_access = CRUDUserFarmAccess(UserFarmAccess)
