# app/schemas/animal_feeding_pivot.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, ForwardRef
from datetime import datetime
import uuid
from decimal import Decimal

# Importa los schemas reducidos de las entidades relacionadas si es necesario para relaciones internas del pivote
from app.schemas.animal import AnimalReduced
from app.schemas.feeding import FeedingReduced

# --- Esquemas Reducidos para AnimalFeedingPivot ---
class AnimalFeedingPivotReduced(BaseModel):
    animal_id: uuid.UUID
    feeding_event_id: uuid.UUID
    quantity_fed: Optional[Decimal] = None
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación (usado principalmente internamente por Feeding CRUD) ---
class AnimalFeedingPivotCreate(BaseModel):
    animal_id: uuid.UUID = Field(..., description="ID of the animal involved in this feeding event")
    feeding_event_id: uuid.UUID = Field(..., description="ID of the feeding event")
    quantity_fed: Optional[Decimal] = Field(None, gt=0, description="Specific quantity fed to this animal, if different from the event's total quantity")
    notes: Optional[str] = Field(None, description="Notes specific to this animal's participation in the feeding event")

    model_config = ConfigDict(from_attributes=True)

# --- Esquema de Lectura/Respuesta (con relaciones opcionales) ---
class AnimalFeedingPivot(BaseModel):
    animal_id: uuid.UUID
    feeding_event_id: uuid.UUID
    quantity_fed: Optional[Decimal] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Se pueden incluir versiones reducidas de las entidades relacionadas si es necesario
    # para evitar recursión al cargar el pivote directamente.
    animal: Optional[AnimalReduced] = None
    feeding_event: Optional[FeedingReduced] = None

    model_config = ConfigDict(from_attributes=True)
