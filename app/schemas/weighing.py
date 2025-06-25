# app/schemas/weighing.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime
import uuid
from decimal import Decimal

# Importa los schemas reducidos de las entidades relacionadas
from app.schemas.user import UserReduced
from app.schemas.animal import AnimalReduced

# --- Esquemas Reducidos para Weighing ---
class WeighingReduced(BaseModel):
    id: uuid.UUID
    animal_id: uuid.UUID
    weighing_date: datetime
    weight_kg: Decimal
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación/Actualización ---
class WeighingBase(BaseModel):
    animal_id: uuid.UUID = Field(..., description="ID of the animal being weighed")
    weighing_date: datetime = Field(default_factory=datetime.utcnow, description="Date and time of the weighing")
    weight_kg: Decimal = Field(..., gt=0, description="Weight of the animal in kilograms (greater than 0)")
    notes: Optional[str] = Field(None, description="Any specific notes about the weighing")

    model_config = ConfigDict(from_attributes=True)

class WeighingCreate(WeighingBase):
    pass

class WeighingUpdate(WeighingBase):
    # Todos los campos opcionales para permitir actualizaciones parciales
    animal_id: Optional[uuid.UUID] = None
    weighing_date: Optional[datetime] = None
    weight_kg: Optional[Decimal] = Field(None, gt=0)
    notes: Optional[str] = None

# --- Esquema de Lectura/Respuesta (con relaciones) ---
class Weighing(WeighingBase):
    id: uuid.UUID
    recorded_by_user_id: uuid.UUID
    created_at: datetime # Heredado de BaseModel
    updated_at: datetime # Heredado de BaseModel

    # Relaciones directas (cargadas para la respuesta)
    animal: Optional[AnimalReduced] = None
    recorded_by_user: Optional[UserReduced] = None

    model_config = ConfigDict(from_attributes=True)
