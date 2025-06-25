# app/schemas/transaction.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime
import uuid
from decimal import Decimal

# Importa los schemas reducidos de las entidades relacionadas
from app.schemas.user import UserReduced
from app.schemas.master_data import MasterDataReduced
from app.schemas.farm import FarmReduced

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
    transaction_type_id: uuid.UUID = Field(..., description="ID of the MasterData entry for the transaction type (e.g., 'sale', 'purchase', 'expense')")
    entity_type: str = Field(..., description="Type of entity associated with the transaction (e.g., 'Animal', 'Product', 'Batch', 'Other')")
    entity_id: uuid.UUID = Field(..., description="ID of the specific entity associated with the transaction")
    quantity: Optional[Decimal] = Field(None, gt=0, description="Quantity of the item or service transacted (greater than 0)")
    unit_id: Optional[uuid.UUID] = Field(None, description="ID of the MasterData entry for the unit of measure (e.g., 'kg', 'unit')")
    price_per_unit: Optional[Decimal] = Field(None, gt=0, description="Price per unit of the item or service (greater than 0)")
    total_amount: Optional[Decimal] = Field(None, gt=0, description="Total amount of the transaction (quantity * price_per_unit, or direct input) (greater than 0)")
    currency_id: Optional[uuid.UUID] = Field(None, description="ID of the MasterData entry for the currency used (e.g., 'USD', 'CRC')")
    notes: Optional[str] = Field(None, description="Any additional notes about the transaction")
    source_farm_id: Optional[uuid.UUID] = Field(None, description="ID of the farm from which the entity originated (e.g., for sales/transfers)")
    destination_farm_id: Optional[uuid.UUID] = Field(None, description="ID of the farm where the entity is going (e.g., for purchases/transfers)")

    model_config = ConfigDict(from_attributes=True)

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(TransactionBase):
    # Permite que todos los campos de TransactionBase sean opcionales para una actualización parcial
    transaction_date: Optional[datetime] = None
    transaction_type_id: Optional[uuid.UUID] = None
    entity_type: Optional[str] = None
    entity_id: Optional[uuid.UUID] = None
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_id: Optional[uuid.UUID] = None
    price_per_unit: Optional[Decimal] = Field(None, gt=0)
    total_amount: Optional[Decimal] = Field(None, gt=0)
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


    model_config = ConfigDict(from_attributes=True)
