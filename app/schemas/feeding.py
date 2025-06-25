# app/schemas/feeding.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime
import uuid
from decimal import Decimal

# Importa los schemas reducidos de las entidades relacionadas
from app.schemas.user import UserReduced
from app.schemas.master_data import MasterDataReduced

# ForwardRef para AnimalFeedingPivotReduced
AnimalFeedingPivotReduced = ForwardRef('AnimalFeedingPivotReduced')

# --- Esquemas Reducidos para Feeding ---
class FeedingReduced(BaseModel):
    id: uuid.UUID
    feeding_date: datetime
    feed_type_id: uuid.UUID
    quantity: Decimal
    unit_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación/Actualización ---
class FeedingBase(BaseModel):
    feeding_date: datetime = Field(default_factory=datetime.utcnow, description="Date and time the feeding occurred")
    feed_type_id: uuid.UUID = Field(..., description="ID of the MasterData entry for the type of feed (e.g., 'concentrate', 'pasture')")
    quantity: Decimal = Field(..., gt=0, description="Total quantity of feed administered (greater than 0)")
    unit_id: uuid.UUID = Field(..., description="ID of the MasterData entry for the unit of measure (e.g., 'kg', 'lb')")
    notes: Optional[str] = Field(None, description="Any specific notes about the feeding event")

    model_config = ConfigDict(from_attributes=True)

class FeedingCreate(FeedingBase):
    # Campo para asociar animales al momento de la creación
    animal_ids: List[uuid.UUID] = Field(default_factory=list, description="List of Animal IDs to associate with this feeding event")

class FeedingUpdate(FeedingBase):
    # Permite que todos los campos de FeedingBase sean opcionales para una actualización parcial
    feeding_date: Optional[datetime] = None
    feed_type_id: Optional[uuid.UUID] = None
    # Corrección aquí: decimal_places ya no es un argumento directo de Field()
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    
    # Para actualizar las asociaciones de animales, si es necesario
    animal_ids: Optional[List[uuid.UUID]] = Field(None, description="List of Animal IDs to update associations for this feeding event (replaces existing)")

# --- Esquema de Lectura/Respuesta (con relaciones) ---
class Feeding(FeedingBase):
    id: uuid.UUID
    recorded_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    # Relaciones directas (cargadas para la respuesta)
    feed_type: Optional[MasterDataReduced] = None
    unit: Optional[MasterDataReduced] = None
    recorded_by_user: Optional[UserReduced] = None
    animal_feedings: List[AnimalFeedingPivotReduced] = [] # Lista de pivotes de animales asociados

    model_config = ConfigDict(from_attributes=True)
