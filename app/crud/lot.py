# app/crud/lot.py
from typing import Optional, List, Union, Dict, Any # Añadido Union, Dict, Any
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError as DBIntegrityError # Importa la excepción de integridad de SQLAlchemy


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
        existing_lot_q = await db.execute(
            select(Lot).filter(Lot.name == obj_in.name, Lot.farm_id == obj_in.farm_id)
        )
        if existing_lot_q.scalar_one_or_none():
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
        except DBIntegrityError as e: # Captura errores de integridad de la DB
            await db.rollback()
            raise AlreadyExistsError(f"Error de integridad al crear Lot: {e}") from e
        except Exception as e:
            await db.rollback()
            if isinstance(e, AlreadyExistsError): # Re-lanza la excepción AlreadyExistsError si ya la manejaste
                raise e
            raise CRUDException(f"Error creating Lot: {str(e)}") from e

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[Lot]: # Cambiado lot_id a id
        """
        Obtiene un lote por su ID, cargando la relación con la finca.
        """
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.farm)) # Carga la relación 'farm'
            .filter(self.model.id == id) # Cambiado lot_id a id
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

    async def get_by_farm_id_and_name(self, db: AsyncSession, farm_id: uuid.UUID, name: str) -> Optional[Lot]:
        """
        Obtiene un lote por el ID de la finca y el nombre del lote.
        """
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.farm))
            .filter(Lot.name == name, Lot.farm_id == farm_id)
        )
        return result.scalar_one_or_none()


    async def update(self, db: AsyncSession, *, db_obj: Lot, obj_in: Union[LotUpdate, Dict[str, Any]]) -> Lot: # Añadido Union, Dict, Any
        """
        Actualiza un lote existente.
        Después de la actualización, recarga el objeto con las relaciones necesarias.
        """
        try:
            # Si obj_in es un Pydantic model, conviértelo a dict y excluye unset
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)
            
            # Si se intenta cambiar el farm_id, valida que la nueva finca exista
            if "farm_id" in update_data and update_data["farm_id"] != db_obj.farm_id:
                # Aquí podrías añadir una validación para asegurar que la nueva finca existe
                # from app.models.farm import Farm # Importar aquí para evitar circular dependency
                # new_farm_q = await db.execute(select(Farm).filter(Farm.id == update_data["farm_id"]))
                # if not new_farm_q.scalar_one_or_none():
                #     raise NotFoundError(f"Farm with ID {update_data['farm_id']} not found.")
                pass # Eliminado la validación si se requiere que sea manejada en el router/endpoint

            # Si el nombre se está actualizando, verifica unicidad dentro de la misma finca
            if "name" in update_data and update_data["name"] != db_obj.name:
                existing_lot_with_new_name_q = await db.execute(
                    select(Lot).filter(
                        Lot.name == update_data["name"], 
                        Lot.farm_id == db_obj.farm_id, # Usar la farm_id original del objeto DB
                        Lot.id != db_obj.id # Excluir el propio lote que estamos actualizando
                    )
                )
                if existing_lot_with_new_name_q.scalar_one_or_none():
                    raise AlreadyExistsError(f"Lot with name '{update_data['name']}' already exists for farm ID '{db_obj.farm_id}'.")

            updated_lot = await super().update(db, db_obj=db_obj, obj_in=update_data)
            if updated_lot:
                # Recarga el objeto actualizado con las relaciones si es necesario para la respuesta
                result = await db.execute(
                    select(self.model)
                    .options(selectinload(self.model.farm))
                    .filter(self.model.id == updated_lot.id)
                )
                return result.scalars().first()
            return updated_lot
        except Exception as e:
            await db.rollback()
            if isinstance(e, NotFoundError) or isinstance(e, AlreadyExistsError) or isinstance(e, CRUDException):
                raise e
            raise CRUDException(f"Error updating Lot: {str(e)}") from e

    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[Lot]: # Cambiado delete a remove
        """
        Elimina un lote por su ID.
        """
        db_obj = await self.get(db, id)
        if not db_obj:
            raise NotFoundError(f"Lot with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting Lot: {str(e)}") from e

# Crea una instancia de CRUDLot que se puede importar y usar en los routers
lot = CRUDLot(Lot)
