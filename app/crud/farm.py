# app/crud/farm.py
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.crud.base import CRUDBase
from app.models.farm import Farm
from app.schemas.farm import FarmCreate, FarmUpdate

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


# Crea una instancia de CRUDFarm que será importada y usada en otros módulos.
farm = CRUDFarm(Farm)

