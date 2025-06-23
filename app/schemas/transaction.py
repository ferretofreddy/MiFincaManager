# app/schemas/transaction.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime
import uuid
from decimal import Decimal # Importa Decimal

# Importa los schemas reducidos de las entidades relacionadas
from app.schemas.user import UserReduced
from app.schemas.master_data import MasterDataReduced
from app.schemas.farm import FarmReduced

# Si se desea cargar AnimalReduced, ProductReduced, BatchReduced en el futuro,
# se importarían aquí y se manejaría la lógica en el esquema de lectura.
# from app.schemas.animal import AnimalReduced
# from app.schemas.product import ProductReduced # Asumiendo que tendrás un modelo Product
# from app.schemas.batch import BatchReduced # Asumiendo que tendrás un modelo Batch

# --- Esquemas Reducidos para Transaction ---
class TransactionReduced(BaseModel):
    id: uuid.UUID
    transaction_date: datetime
    transaction_type_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    total_amount: Optional[Decimal] = None
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación/Actualización ---
class TransactionBase(BaseModel):
    transaction_date: datetime = Field(default_factory=datetime.utcnow, description="Date and time of the transaction")
    transaction_type_id: uuid.UUID = Field(..., description="ID of the MasterData entry for the transaction type (e.g., 'purchase', 'sale', 'transfer')")
    entity_type: str = Field(..., description="Type of entity involved in the transaction (e.g., 'Animal', 'Product', 'Batch')")
    entity_id: uuid.UUID = Field(..., description="ID of the specific entity involved in the transaction")
    quantity: Optional[Decimal] = Field(None, gt=0, decimal_places=2, description="Quantity if applicable (e.g., kg of meat, number of animals)")
    unit_id: Optional[uuid.UUID] = Field(None, description="ID of the MasterData entry for the unit of measure (e.g., 'kg', 'unit')")
    price_per_unit: Optional[Decimal] = Field(None, gt=0, decimal_places=2, description="Price per unit of the entity")
    total_amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2, description="Total amount of the transaction")
    currency_id: Optional[uuid.UUID] = Field(None, description="ID of the MasterData entry for the currency (e.g., 'USD', 'CRC')")
    notes: Optional[str] = Field(None, description="Any specific notes about the transaction")
    source_farm_id: Optional[uuid.UUID] = Field(None, description="ID of the source farm for the transaction (if applicable)")
    destination_farm_id: Optional[uuid.UUID] = Field(None, description="ID of the destination farm for the transaction (if applicable)")

    model_config = ConfigDict(from_attributes=True)

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(TransactionBase):
    # Todos los campos opcionales para permitir actualizaciones parciales
    transaction_date: Optional[datetime] = None
    transaction_type_id: Optional[uuid.UUID] = None
    entity_type: Optional[str] = None
    entity_id: Optional[uuid.UUID] = None
    quantity: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    unit_id: Optional[uuid.UUID] = None
    price_per_unit: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    total_amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    currency_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    source_farm_id: Optional[uuid.UUID] = None
    destination_farm_id: Optional[uuid.UUID] = None

# --- Esquema de Lectura/Respuesta (con relaciones) ---
class Transaction(TransactionBase):
    id: uuid.UUID
    recorded_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    # Relaciones directas (cargadas para la respuesta)
    transaction_type: Optional[MasterDataReduced] = None
    unit: Optional[MasterDataReduced] = None
    currency: Optional[MasterDataReduced] = None
    recorded_by_user: Optional[UserReduced] = None
    source_farm: Optional[FarmReduced] = None
    destination_farm: Optional[FarmReduced] = None

    # El campo `entity_details` se agregaría para cargar dinámicamente los detalles
    # de la entidad relacionada (Animal, Product, Batch) después de obtener la transacción.
    # Esto se manejaría en el servicio/router, no directamente en Pydantic con `model_config`.
    # entity_details: Optional[Union[AnimalReduced, ProductReduced, BatchReduced]] = None

    model_config = ConfigDict(from_attributes=True)

# Reconstruir los modelos para resolver ForwardRefs
TransactionReduced.model_rebuild()
Transaction.model_rebuild()
