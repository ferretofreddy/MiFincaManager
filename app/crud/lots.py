# app/crud/lots.py
from typing import Optional, List
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

# Importa el modelo Lot y los esquemas de lot
from app.models.lot import Lot
from app.schemas.lot import LotCreate, LotUpdate

# Importa la CRUDBase y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, AlreadyExistsError, CRUDException

class CRUDLot(CRUDBase[Lot, LotCreate, LotUpdate]):
    """
    Clase CRUD específica para el modelo Lot.
    Hereda la mayoría de las operaciones de CRUDBase.
    Implementa métodos específicos para Lot que requieren lógica adicional
    (ej. carga de relaciones, verificación de unicidad).
    """

    async def create(self, db: AsyncSession, *, obj_in: LotCreate) -> Lot:
        """
        Crea un nuevo lote.
        Verifica la unicidad del nombre del lote dentro de la misma finca.
        """
        # Verifica si ya existe un lote con el mismo nombre en la misma finca
        existing_lot = await db.execute(
            select(Lot).filter(Lot.name == obj_in.name, Lot.farm_id == obj_in.farm_id)
        )
        if existing_lot.scalar_one_or_none():
            raise AlreadyExistsError(f"Lot with name '{obj_in.name}' already exists for farm ID '{obj_in.farm_id}'.")

        try:
            db_obj = self.model(**obj_in.model_dump())
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj) # Obtiene el ID, created_at, updated_at
            
            # Recarga el lote con la relación farm para la respuesta
            result = await db.execute(
                select(Lot)
                .options(selectinload(Lot.farm)) # Carga la relación 'farm'
                .filter(Lot.id == db_obj.id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error creating Lot: {str(e)}") from e

    async def get(self, db: AsyncSession, lot_id: uuid.UUID) -> Optional[Lot]:
        """
        Obtiene un lote por su ID, cargando la relación con la finca.
        """
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.farm)) # Carga la relación 'farm'
            .filter(self.model.id == lot_id)
        )
        return result.scalar_one_or_none()

    async def get_multi_by_farm(self, db: AsyncSession, farm_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Lot]:
        """
        Obtiene una lista de lotes por el ID de la finca a la que pertenecen.
        """
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.farm)) # Carga la relación 'farm'
            .filter(self.model.farm_id == farm_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, db: AsyncSession, *, db_obj: Lot, obj_in: LotUpdate) -> Lot:
        """
        Actualiza un lote existente.
        Después de la actualización, recarga el objeto con las relaciones necesarias.
        """
        updated_lot = await super().update(db, db_obj=db_obj, obj_in=obj_in)
        if updated_lot:
            # Recarga el objeto actualizado con las relaciones si es necesario para la respuesta
            result = await db.execute(
                select(self.model)
                .options(selectinload(self.model.farm))
                .filter(self.model.id == updated_lot.id)
            )
            return result.scalar_one_or_none()
        return updated_lot

# Crea una instancia de CRUDLot que se puede importar y usar en los routers
lot = CRUDLot(Lot)
