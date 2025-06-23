# app/schemas/master_data.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, ForwardRef # Añade Dict y Any para 'properties'
from datetime import datetime
import uuid

# Importa UserReduced de tu nuevo módulo de schemas de usuario
from app.schemas.user import UserReduced

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

    created_by_user: Optional[UserReduced] = None # Usa el esquema reducido de User

    # Aquí irían las relaciones inversas a AnimalReduced, GrupoReduced, etc.
    # Por ahora las dejamos como ForwardRef, pero deberás migrarlas y luego quitarlas.
    animals_species: List[ForwardRef('AnimalReduced')] = [] # Si AnimalReduced existe
    animals_breed: List[ForwardRef('AnimalReduced')] = []
    grupos_purpose: List[ForwardRef('GrupoReduced')] = []
    feedings_feed_type: List[ForwardRef('FeedingReduced')] = []
    feedings_supplement: List[ForwardRef('FeedingReduced')] = []
    health_events_product: List[ForwardRef('HealthEventReduced')] = []
    transaction_record_type: List[ForwardRef('TransactionReduced')] = []
    parameter_data_type: List[ForwardRef('ConfigurationParameterReduced')] = []


    model_config = ConfigDict(from_attributes=True)

# Reconstruir los modelos para resolver ForwardRefs (si los hay)
MasterDataReduced.model_rebuild()
MasterData.model_rebuild()
