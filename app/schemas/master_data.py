# app/schemas/master_data.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, ForwardRef # Añade Dict y Any para 'properties'
from datetime import datetime
import uuid

# Define ForwardRef para esquemas si hay circularidad
UserReduced = ForwardRef("UserReduced")
AnimalReduced = ForwardRef("AnimalReduced") # Asegúrate que estén aquí si se usan en MasterData
GrupoReduced = ForwardRef("GrupoReduced")
FeedingReduced = ForwardRef("FeedingReduced")
HealthEventReduced = ForwardRef("HealthEventReduced")
TransactionReduced = ForwardRef("TransactionReduced")
BatchReduced = ForwardRef("BatchReduced")
ProductReduced = ForwardRef("ProductReduced")

# ¡AÑADE ESTA LÍNEA!
ConfigurationParameterReduced = ForwardRef("ConfigurationParameterReduced")

# --- Esquemas Reducidos (MasterDataReduced se queda aquí) ---
class MasterDataReduced(BaseModel):
    id: uuid.UUID
    category: str
    name: str
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación/Actualización ---
class MasterDataBase(BaseModel):
    category: str = Field(..., description="Category of the master data (e.g., 'species', 'breed', 'event_type')")
    name: str = Field(..., description="Name of the master data entry")
    description: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None # Para JSONB, usa Dict[str, Any]
    is_active: Optional[bool] = True

class MasterDataCreate(MasterDataBase):
    pass # No necesita campos adicionales para la creación

class MasterDataUpdate(MasterDataBase):
    category: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

# --- Esquema de Lectura/Respuesta (con relaciones) ---
class MasterData(MasterDataBase):
    id: uuid.UUID
    created_by_user_id: uuid.UUID
    created_at: datetime # Heredado de BaseModel
    updated_at: datetime # Heredado de BaseModel

    created_by_user: Optional["UserReduced"] = None # Usa el esquema reducido de User

    # Relaciones inversas (asegúrate de que estén usando ForwardRef como string)
    animals_species: List["AnimalReduced"] = []
    animals_breed: List["AnimalReduced"] = []
    grupos_purpose: List["GrupoReduced"] = []
    feedings_feed_type: List["FeedingReduced"] = []
    feedings_supplement: List["FeedingReduced"] = []
    health_events_product: List["HealthEventReduced"] = []
    transaction_record_type: List["TransactionReduced"] = []
    
    # ¡ASEGÚRATE QUE ESTA REFERENCIA ESTÉ COMO STRING!
    parameter_data_type: List["ConfigurationParameterReduced"] = [] # Nueva relación

    # Si hay otras relaciones inversas, asegúrate de que usen ForwardRef como string:
    batches_batch_type: List["BatchReduced"] = []
    products_as_type: List["ProductReduced"] = []
    products_as_unit: List["ProductReduced"] = []
    transactions_unit: List["TransactionReduced"] = []
    transactions_currency: List["TransactionReduced"] = []
    # Añade aquí cualquier otra relación inversa que MasterData pueda tener

    model_config = ConfigDict(from_attributes=True)
