# app/schemas/animal_batch_pivot.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, ForwardRef
from datetime import datetime
import uuid

# Importa los schemas reducidos de las entidades relacionadas si es necesario
from app.schemas.animal import AnimalReduced # Para AnimalBatchPivot si necesitamos cargar el Animal
from app.schemas.batch import BatchReduced # Para AnimalBatchPivot si necesitamos cargar el Batch

# --- Esquemas Reducidos para AnimalBatchPivot ---
class AnimalBatchPivotReduced(BaseModel):
    animal_id: uuid.UUID
    batch_event_id: uuid.UUID
    assigned_date: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación (usado principalmente internamente por Batch CRUD) ---
class AnimalBatchPivotCreate(BaseModel):
    animal_id: uuid.UUID = Field(..., description="ID of the animal assigned to this batch")
    batch_event_id: uuid.UUID = Field(..., description="ID of the batch event")
    assigned_date: datetime = Field(default_factory=datetime.utcnow, description="Date when the animal was assigned to the batch")
    notes: Optional[str] = Field(None, description="Notes specific to this animal's assignment to the batch")

    model_config = ConfigDict(from_attributes=True)

# --- Esquema de Lectura/Respuesta (con relaciones opcionales) ---
class AnimalBatchPivot(BaseModel):
    animal_id: uuid.UUID
    batch_event_id: uuid.UUID
    assigned_date: datetime
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Se pueden incluir versiones reducidas de las entidades relacionadas si es necesario
    animal: Optional[AnimalReduced] = None
    batch_event: Optional[BatchReduced] = None # Usar la versión reducida de Batch

    model_config = ConfigDict(from_attributes=True)

# Reconstruir los modelos para resolver ForwardRefs
AnimalBatchPivotReduced.model_rebuild()
AnimalBatchPivot.model_rebuild()
