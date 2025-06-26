# app/crud/transaction.py
from typing import Optional, List, Union, Dict, Any
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError as DBIntegrityError

# Importa el modelo Transaction y los esquemas
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate

# Importa modelos para validación de IDs foráneos
from app.models.master_data import MasterData
from app.models.farm import Farm
from app.models.animal import Animal
from app.models.product import Product
from app.models.batch import Batch

# Importa la CRUDBase y las excepciones
from app.crud.base import CRUDBase
from app.crud.exceptions import NotFoundError, CRUDException, AlreadyExistsError

class CRUDTransaction(CRUDBase[Transaction, TransactionCreate, TransactionUpdate]):
    """
    Clase CRUD específica para el modelo Transaction.
    Gestiona los registros de transacciones.
    """

    async def _validate_foreign_keys(self, db: AsyncSession, obj_in: Union[TransactionCreate, TransactionUpdate]):
        """
        Valida que los IDs foráneos de MasterData y Farm existan, y si entity_id/entity_type_id son válidos.
        """
        if obj_in.transaction_type_id:
            md_type_q = await db.execute(select(MasterData).filter(MasterData.id == obj_in.transaction_type_id))
            md_type = md_type_q.scalar_one_or_none()
            if not md_type:
                raise NotFoundError(f"MasterData with ID {obj_in.transaction_type_id} (transaction_type) not found.")
            if md_type.category != "transaction_type":
                raise CRUDException(f"MasterData with ID {obj_in.transaction_type_id} is not of category 'transaction_type'.")

        if obj_in.unit_id:
            md_unit_q = await db.execute(select(MasterData).filter(MasterData.id == obj_in.unit_id))
            md_unit = md_unit_q.scalar_one_or_none()
            if not md_unit:
                raise NotFoundError(f"MasterData with ID {obj_in.unit_id} (unit_id) not found.")
            if md_unit.category != "unit_of_measure":
                raise CRUDException(f"MasterData with ID {obj_in.unit_id} is not of category 'unit_of_measure'.")

        if obj_in.currency_id:
            md_currency_q = await db.execute(select(MasterData).filter(MasterData.id == obj_in.currency_id))
            md_currency = md_currency_q.scalar_one_or_none()
            if not md_currency:
                raise NotFoundError(f"MasterData with ID {obj_in.currency_id} (currency_id) not found.")
            if md_currency.category != "currency":
                raise CRUDException(f"MasterData with ID {obj_in.currency_id} is not of category 'currency'.")
        
        if obj_in.source_farm_id:
            source_farm_q = await db.execute(select(Farm).filter(Farm.id == obj_in.source_farm_id))
            if not source_farm_q.scalar_one_or_none():
                raise NotFoundError(f"Source Farm with ID {obj_in.source_farm_id} not found.")

        if obj_in.destination_farm_id:
            destination_farm_q = await db.execute(select(Farm).filter(Farm.id == obj_in.destination_farm_id))
            if not destination_farm_q.scalar_one_or_none():
                raise NotFoundError(f"Destination Farm with ID {obj_in.destination_farm_id} not found.")

        # Validar entity_id y entity_type_id
        if obj_in.entity_id and obj_in.entity_type_id: # Ahora esperamos entity_type_id
            # Validar que entity_type_id sea un MasterData de tipo 'entity_type'
            md_entity_type_q = await db.execute(select(MasterData).filter(MasterData.id == obj_in.entity_type_id))
            md_entity_type = md_entity_type_q.scalar_one_or_none()
            if not md_entity_type:
                raise NotFoundError(f"MasterData with ID {obj_in.entity_type_id} (entity_type) not found.")
            if md_entity_type.category != "entity_type":
                raise CRUDException(f"MasterData with ID {obj_in.entity_type_id} is not of category 'entity_type'.")

            # Luego, validar que entity_id exista según el entity_type (nombre del MasterData)
            if md_entity_type.name == "Animal":
                animal_q = await db.execute(select(Animal).filter(Animal.id == obj_in.entity_id))
                if not animal_q.scalar_one_or_none():
                    raise NotFoundError(f"Animal with ID {obj_in.entity_id} (entity_id) not found for entity type 'Animal'.")
            elif md_entity_type.name == "Product":
                product_q = await db.execute(select(Product).filter(Product.id == obj_in.entity_id))
                if not product_q.scalar_one_or_none():
                    raise NotFoundError(f"Product with ID {obj_in.entity_id} (entity_id) not found for entity type 'Product'.")
            elif md_entity_type.name == "Batch":
                batch_q = await db.execute(select(Batch).filter(Batch.id == obj_in.entity_id))
                if not batch_q.scalar_one_or_none():
                    raise NotFoundError(f"Batch with ID {obj_in.entity_id} (entity_id) not found for entity type 'Batch'.")
            else:
                raise CRUDException(f"Validation for entity_type '{md_entity_type.name}' not implemented or invalid.")
        elif obj_in.entity_id or obj_in.entity_type_id:
            raise CRUDException("Both 'entity_id' and 'entity_type_id' must be provided if either is present.")

    async def create(self, db: AsyncSession, *, obj_in: TransactionCreate, recorded_by_user_id: uuid.UUID) -> Transaction:
        """
        Crea un nuevo registro de transacción.
        """
        try:
            await self._validate_foreign_keys(db, obj_in)

            db_transaction = self.model(**obj_in.model_dump(), recorded_by_user_id=recorded_by_user_id)
            db.add(db_transaction)
            await db.commit()
            await db.refresh(db_transaction)
            
            result = await db.execute(
                select(Transaction)
                .options(
                    selectinload(Transaction.transaction_type),
                    selectinload(Transaction.entity_type_md), # Cargar la relación para entity_type_id
                    selectinload(Transaction.unit),
                    selectinload(Transaction.currency),
                    selectinload(Transaction.recorded_by_user),
                    selectinload(Transaction.source_farm),
                    selectinload(Transaction.destination_farm)
                )
                .filter(Transaction.id == db_transaction.id)
            )
            return result.scalars().first()
        except DBIntegrityError as e:
            await db.rollback()
            raise AlreadyExistsError(f"Error de integridad al crear Transaction record: {e}") from e
        except Exception as e:
            await db.rollback()
            if isinstance(e, (NotFoundError, AlreadyExistsError, CRUDException)):
                raise e
            raise CRUDException(f"Error creating Transaction record: {str(e)}") from e

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[Transaction]:
        """
        Obtiene un registro de transacción por su ID, cargando las relaciones.
        """
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.transaction_type),
                selectinload(self.model.entity_type_md), # Cargar la relación para entity_type_id
                selectinload(self.model.unit),
                selectinload(self.model.currency),
                selectinload(self.model.recorded_by_user),
                selectinload(self.model.source_farm),
                selectinload(self.model.destination_farm)
            )
            .filter(self.model.id == id)
        )
        return result.scalars().first()

    async def get_multi_by_filters(
        self, 
        db: AsyncSession, 
        recorded_by_user_id: Optional[uuid.UUID] = None,
        source_farm_id: Optional[uuid.UUID] = None,
        destination_farm_id: Optional[uuid.UUID] = None,
        entity_id: Optional[uuid.UUID] = None,
        entity_type_id: Optional[uuid.UUID] = None, # Ahora filtro por entity_type_id
        transaction_type_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Transaction]:
        """
        Obtiene múltiples registros de transacción con filtros opcionales.
        """
        query = select(self.model).options(
            selectinload(self.model.transaction_type),
            selectinload(self.model.entity_type_md), # Cargar la relación para entity_type_id
            selectinload(self.model.unit),
            selectinload(self.model.currency),
            selectinload(self.model.recorded_by_user),
            selectinload(self.model.source_farm),
            selectinload(self.model.destination_farm)
        )

        filters = []
        if recorded_by_user_id:
            filters.append(self.model.recorded_by_user_id == recorded_by_user_id)
        if source_farm_id:
            filters.append(self.model.source_farm_id == source_farm_id)
        if destination_farm_id:
            filters.append(self.model.destination_farm_id == destination_farm_id)
        if transaction_type_id:
            filters.append(self.model.transaction_type_id == transaction_type_id)
        
        if entity_id:
            filters.append(self.model.entity_id == entity_id)
        if entity_type_id: # Ahora filtro por entity_type_id
            filters.append(self.model.entity_type_id == entity_type_id)

        if start_date:
            filters.append(self.model.transaction_date >= start_date)
        if end_date:
            filters.append(self.model.transaction_date <= end_date)

        if filters:
            query = query.filter(and_(*filters))

        result = await db.execute(query.order_by(self.model.transaction_date.desc()).offset(skip).limit(limit))
        return result.scalars().all()


    async def update(self, db: AsyncSession, *, db_obj: Transaction, obj_in: Union[TransactionUpdate, Dict[str, Any]]) -> Transaction:
        """
        Actualiza un registro de transacción existente.
        """
        try:
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)
            
            temp_obj_in = TransactionUpdate(
                transaction_type_id=update_data.get("transaction_type_id", db_obj.transaction_type_id),
                entity_type_id=update_data.get("entity_type_id", db_obj.entity_type_id), # Ahora usamos entity_type_id
                entity_id=update_data.get("entity_id", db_obj.entity_id),
                unit_id=update_data.get("unit_id", db_obj.unit_id),
                currency_id=update_data.get("currency_id", db_obj.currency_id),
                source_farm_id=update_data.get("source_farm_id", db_obj.source_farm_id),
                destination_farm_id=update_data.get("destination_farm_id", db_obj.destination_farm_id)
            )
            await self._validate_foreign_keys(db, temp_obj_in)

            updated_transaction = await super().update(db, db_obj=db_obj, obj_in=update_data)
            if updated_transaction:
                result = await db.execute(
                    select(self.model)
                    .options(
                        selectinload(self.model.transaction_type),
                        selectinload(self.model.entity_type_md), # Cargar la relación para entity_type_id
                        selectinload(self.model.unit),
                        selectinload(self.model.currency),
                        selectinload(self.model.recorded_by_user),
                        selectinload(self.model.source_farm),
                        selectinload(self.model.destination_farm)
                    )
                    .filter(self.model.id == updated_transaction.id)
                )
                return result.scalars().first()
            return updated_transaction
        except Exception as e:
            await db.rollback()
            if isinstance(e, NotFoundError) or isinstance(e, AlreadyExistsError) or isinstance(e, CRUDException):
                raise e
            raise CRUDException(f"Error updating Transaction record: {str(e)}") from e


    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[Transaction]:
        """
        Elimina un registro de transacción por su ID.
        """
        db_obj = await self.get(db, id)
        if not db_obj:
            raise NotFoundError(f"Transaction record with id {id} not found.")
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return db_obj
        except Exception as e:
            await db.rollback()
            raise CRUDException(f"Error deleting Transaction record: {str(e)}") from e

transaction = CRUDTransaction(Transaction)
