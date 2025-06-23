# app/schemas/batch.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime
import uuid

# Importa los schemas reducidos de las entidades relacionadas
from app.schemas.user import UserReduced
from app.schemas.master_data import MasterDataReduced
from app.schemas.farm import FarmReduced

# ForwardRef para AnimalBatchPivotReduced
AnimalBatchPivotReduced = ForwardRef('AnimalBatchPivotReduced')

# --- Esquemas Reducidos para Batch ---
class BatchReduced(BaseModel):
    id: uuid.UUID
    name: str
    batch_type_id: uuid.UUID
    status: str
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación/Actualización ---
class BatchBase(BaseModel):
    name: str = Field(..., description="Name or identifier for the batch")
    batch_type_id: uuid.UUID = Field(..., description="ID of the MasterData entry for the batch type (e.g., 'sale', 'fattening', 'treatment')")
    description: Optional[str] = Field(None, description="Detailed description of the batch's purpose or contents")
    start_date: datetime = Field(default_factory=datetime.utcnow, description="Date when the batch was created or started")
    end_date: Optional[datetime] = Field(None, description="Date when the batch was concluded or disbanded (optional)")
    status: str = Field(..., description="Current status of the batch (e.g., 'active', 'completed', 'cancelled')")
    farm_id: uuid.UUID = Field(..., description="ID of the farm to which this batch belongs")

    model_config = ConfigDict(from_attributes=True)

class BatchCreate(BatchBase):
    # Campo para asociar animales al momento de la creación
    animal_ids: List[uuid.UUID] = Field(default_factory=list, description="List of Animal IDs to initially include in this batch")

class BatchUpdate(BatchBase):
    # Permite que todos los campos de BatchBase sean opcionales para una actualización parcial
    name: Optional[str] = None
    batch_type_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    farm_id: Optional[uuid.UUID] = None
    
    # Para actualizar las asociaciones de animales, si es necesario
    animal_ids: Optional[List[uuid.UUID]] = Field(None, description="List of Animal IDs to update associations for this batch (replaces existing)")

# --- Esquema de Lectura/Respuesta (con relaciones) ---
class Batch(BatchBase):
    id: uuid.UUID
    created_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    # Relaciones directas (cargadas para la respuesta)
    batch_type: Optional[MasterDataReduced] = None
    farm: Optional[FarmReduced] = None
    created_by_user: Optional[UserReduced] = None
    animal_batches: List[AnimalBatchPivotReduced] = [] # Lista de pivotes de animales asociados

    model_config = ConfigDict(from_attributes=True)

# Reconstruir los modelos para resolver ForwardRefs
BatchReduced.model_rebuild()
BatchCreate.model_rebuild() # Puede que necesite si animal_ids es un ForwardRef
BatchUpdate.model_rebuild() # Puede que necesite si animal_ids es un ForwardRef
Batch.model_rebuild()
