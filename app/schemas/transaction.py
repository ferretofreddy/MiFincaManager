# app/schemas/transaction.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef # 'List' y 'ForwardRef' pueden ser innecesarios si solo usas 'Optional' y no listas de schemas

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
    # Cambiado de entity_type a entity_type_id en el reducido
    entity_type_id: uuid.UUID 
    entity_id: uuid.UUID
    total_amount: Optional[Decimal] = None
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación/Actualización ---
class TransactionBase(BaseModel):
    transaction_date: datetime = Field(default_factory=datetime.utcnow, description="Date and time of the transaction")
    transaction_type_id: uuid.UUID = Field(..., description="ID of the MasterData entry for the transaction type (e.g., 'sale', 'purchase', 'expense')")
    
    # === ¡CAMBIADO: entity_type (str) a entity_type_id (UUID)! ===
    entity_type_id: uuid.UUID = Field(..., description="ID of the MasterData entry for the entity type (e.g., 'Animal', 'Product', 'Batch')")
    
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
    
    # === ¡CAMBIADO: entity_type (str) a entity_type_id (UUID)! ===
    entity_type_id: Optional[uuid.UUID] = None
    
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
class Transaction(BaseModel): # Hereda directamente de BaseModel para permitir la inclusión de relaciones
    id: uuid.UUID
    transaction_date: datetime
    transaction_type_id: uuid.UUID
    entity_type_id: uuid.UUID # Asegura que esté aquí también para la respuesta
    entity_id: uuid.UUID
    quantity: Optional[Decimal] = None
    price_per_unit: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    unit_id: Optional[uuid.UUID] = None
    currency_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    recorded_by_user_id: uuid.UUID
    source_farm_id: Optional[uuid.UUID] = None
    destination_farm_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    # Relaciones directas (cargadas para la respuesta)
    transaction_type: Optional[MasterDataReduced] = None
    entity_type_md: Optional[MasterDataReduced] = None # Nuevo campo para la MasterData de entity_type
    unit: Optional[MasterDataReduced] = None
    currency: Optional[MasterDataReduced] = None
    recorded_by_user: Optional[UserReduced] = None
    source_farm: Optional[FarmReduced] = None
    destination_farm: Optional[FarmReduced] = None

    model_config = ConfigDict(from_attributes=True)

# Reconstruir modelos para resolver ForwardRef (si es necesario)
# Ya no es necesario si todas las referencias se resuelven con las importaciones directas
# o si se usan strings literales en las anotaciones de tipo ForwardRef
