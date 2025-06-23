# app/crud/transactions.py
from typing import Optional, List
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_

# Importa el modelo Transaction y los esquemas
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate

# Importa modelos para validación de IDs foráneos
from app.models.master_data import MasterData
from app.models.farm import Farm
from app.models.animal import Animal # Para validar entity_id si entity_type es 'Animal'
# from app.models.product import Product # Si tuvieras un modelo Product
# from app.models.batch import Batch # Si tuvieras un modelo Batch

# Importa la CRUDBase y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, CRUDException

class CRUDTransaction(CRUDBase[Transaction, TransactionCreate, TransactionUpdate]):
    """
    Clase CRUD específica para el modelo Transaction.
    Gestiona los registros de transacciones.
    """

    async def _validate_foreign_keys(self, db: AsyncSession, obj_in: TransactionCreate | TransactionUpdate):
        """
        Valida que los IDs foráneos de MasterData y Farm existan.
        """
        # Validar transaction_type_id
        if obj_in.transaction_type_id:
            md_type = await db.execute(select(MasterData).filter(MasterData.id == obj_in.transaction_type_id))
            if not md_type.scalar_one_or_none():
                raise NotFoundError(f"MasterData with ID {obj_in.transaction_type_id} (transaction_type_id) not found.")
        
        # Validar unit_id
        if obj_in.unit_id:
            md_unit = await db.execute(select(MasterData).filter(MasterData.id == obj_in.unit_id))
            if not md_unit.scalar_one_or_none():
                raise NotFoundError(f"MasterData with ID {obj_in.unit_id} (unit_id) not found.")
        
        # Validar currency_id
        if obj_in.currency_id:
            md_currency = await db.execute(select(MasterData).filter(MasterData.id == obj_in.currency_id))
            if not md_currency.scalar_one_or_none():
                raise NotFoundError(f"MasterData with ID {obj_in.currency_id} (currency_id) not found.")
        
        # Validar source_farm_id
        if obj_in.source_farm_id:
            src_farm = await db.execute(select(Farm).filter(Farm.id == obj_in.source_farm_id))
            if not src_farm.scalar_one_or_none():
                raise NotFoundError(f"Source Farm with ID {obj_in.source_farm_id} not found.")
        
        # Validar destination_farm_id
        if obj_in.destination_farm_id:
            dest_farm = await db.execute(select(Farm).filter(Farm.id == obj_in.destination_farm_id))
            if not dest_farm.scalar_one_or_none():
                raise NotFoundError(f"Destination Farm with ID {obj_in.destination_farm_id} not found.")

        # Validar entity_id basado en entity_type
        if obj_in.entity_id and obj_in.entity_type:
            model_to_check = None
            if obj_in.entity_type == "Animal":
                model_to_check = Animal
            # elif obj_in.entity_type == "Product":
            #     model_to_check = Product
            # elif obj_in.entity_type == "Batch":
            #     model_to_check = Batch
            # Agrega más condiciones para otros tipos de entidad
            
            if model_to_check:
                entity = await db.execute(select(model_to_check).filter(model_to_check.id == obj_in.entity_id))
                if not entity.scalar_one_or_none():
                    raise NotFoundError(f"Entity of type '{obj_in.entity_type}' with ID {obj_in.entity_id} not found.")
            else:
                # Si el entity_type no es reconocido, podrías lanzar un error o ignorar si es aceptable
                raise CRUDException(f"Invalid entity_type: '{obj_in.entity_type}'.")


    async def create(self, db: AsyncSession, *, obj_in: TransactionCreate, recorded_by_user_id: uuid.UUID) -> Transaction:
        """
        Crea un nuevo registro de transacción.
        """
        try:
            # Validar todas las claves foráneas y la entidad asociada
            await self._validate_foreign_keys(db, obj_in)

            db_transaction = self.model(**obj_in.model_dump(), recorded_by_user_id=recorded_by_user_id)
            db.add(db_transaction)
            await db.commit()
            await db.refresh(db_transaction)
            
            # Recargar la transacción con las relaciones
            result = await db.execute(
                select(Transaction)
                .options(
                    selectinload(Transaction.transaction_type),
                    selectinload(Transaction.unit),
                    selectinload(Transaction.currency),
                    selectinload(Transaction.recorded_by_user),
                    selectinload(Transaction.source_farm),
                    selectinload(Transaction.destination_farm)
                )
                .filter(Transaction.id == db_transaction.id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            if isinstance(e, NotFoundError):
                raise e
            raise CRUDException(f"Error creating Transaction record: {str(e)}") from e

    async def get(self, db: AsyncSession, transaction_id: uuid.UUID) -> Optional[Transaction]:
        """
        Obtiene un registro de transacción por su ID, cargando las relaciones.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.transaction_type),
                selectinload(self.model.unit),
                selectinload(self.model.currency),
                selectinload(self.model.recorded_by_user),
                selectinload(self.model.source_farm),
                selectinload(self.model.destination_farm)
            )
            .filter(self.model.id == transaction_id)
        )
        return result.scalar_one_or_none()

    async def get_multi_by_farm_id(self, db: AsyncSession, farm_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Transaction]:
        """
        Obtiene todas las transacciones donde la granja es el origen o el destino.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.transaction_type),
                selectinload(self.model.unit),
                selectinload(self.model.currency),
                selectinload(self.model.recorded_by_user),
                selectinload(self.model.source_farm),
                selectinload(self.model.destination_farm)
            )
            .filter(or_(self.model.source_farm_id == farm_id, self.model.destination_farm_id == farm_id))
            .order_by(self.model.transaction_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_multi_by_entity(self, db: AsyncSession, entity_id: uuid.UUID, entity_type: str, skip: int = 0, limit: int = 100) -> List[Transaction]:
        """
        Obtiene todas las transacciones para una entidad específica (ej. un animal en particular).
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.transaction_type),
                selectinload(self.model.unit),
                selectinload(self.model.currency),
                selectinload(self.model.recorded_by_user),
                selectinload(self.model.source_farm),
                selectinload(self.model.destination_farm)
            )
            .filter(and_(self.model.entity_id == entity_id, self.model.entity_type == entity_type))
            .order_by(self.model.transaction_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


    async def update(self, db: AsyncSession, *, db_obj: Transaction, obj_in: TransactionUpdate) -> Transaction:
        """
        Actualiza un registro de transacción existente.
        """
        try:
            # Validar todas las claves foráneas y la entidad asociada si se proporcionan en la actualización
            await self._validate_foreign_keys(db, obj_in) # Usa obj_in para la validación

            updated_transaction = await super().update(db, db_obj=db_obj, obj_in=obj_in)
            if updated_transaction:
                result = await db.execute(
                    select(self.model)
                    .options(
                        selectinload(self.model.transaction_type),
                        selectinload(self.model.unit),
                        selectinload(self.model.currency),
                        selectinload(self.model.recorded_by_user),
                        selectinload(self.model.source_farm),
                        selectinload(self.model.destination_farm)
                    )
                    .filter(self.model.id == updated_transaction.id)
                )
                return result.scalar_one_or_none()
            return updated_transaction
        except Exception as e:
            await db.rollback()
            if isinstance(e, NotFoundError):
                raise e
            raise CRUDException(f"Error updating Transaction record: {str(e)}") from e


    async def delete(self, db: AsyncSession, *, id: uuid.UUID) -> Transaction:
        """
        Elimina un registro de transacción por su ID.
        """
        db_obj = await self.get(db, id) # Primero obtenemos el objeto para asegurar que existe y para devolverlo
        if not db_obj:
            raise NotFoundError(f"Transaction record with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj # Retorna el objeto eliminado
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting Transaction record: {str(e)}") from e

# Crea una instancia de CRUDTransaction que se puede importar y usar en los routers
transaction = CRUDTransaction(Transaction)
