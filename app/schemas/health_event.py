# app/schemas/health_event.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime
import uuid
from decimal import Decimal # Importa Decimal

# Importa los ENUMS
from app.enums import HealthEventTypeEnumPython

# Importa los schemas reducidos de las entidades relacionadas
from app.schemas.user import UserReduced
from app.schemas.master_data import MasterDataReduced
from app.schemas.animal import AnimalReducedForAnimalGroup # Para AnimalHealthEventPivotReduced

# ForwardRef para AnimalHealthEventPivot
AnimalHealthEventPivotReduced = ForwardRef('AnimalHealthEventPivotReduced')

# --- Esquemas Reducidos para HealthEvent ---
class HealthEventReduced(BaseModel):
    id: uuid.UUID
    event_type: HealthEventTypeEnumPython
    event_date: datetime
    model_config = ConfigDict(from_attributes=True)

class HealthEventReducedForPivot(BaseModel): # Para uso en AnimalHealthEventPivotReduced
    id: uuid.UUID
    event_type: HealthEventTypeEnumPython
    event_date: datetime
    description: Optional[str] = None
    product: Optional[MasterDataReduced] = None
    unit: Optional[MasterDataReduced] = None
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación/Actualización ---
class HealthEventBase(BaseModel):
    event_type: HealthEventTypeEnumPython = Field(..., description="Type of health event (e.g., 'vaccination', 'deworming')")
    event_date: datetime = Field(default_factory=datetime.utcnow, description="Date and time the event occurred")
    description: Optional[str] = Field(None, description="Detailed description of the health event")
    product_id: Optional[uuid.UUID] = Field(None, description="ID of the MasterData product used (e.g., vaccine, medication)")
    quantity: Optional[Decimal] = Field(None, description="Quantity of the product administered")
    unit_id: Optional[uuid.UUID] = Field(None, description="ID of the MasterData unit of measure for the product (e.g., 'ml', 'mg')")

    model_config = ConfigDict(from_attributes=True)

class HealthEventCreate(HealthEventBase):
    animal_ids: List[uuid.UUID] = Field(..., description="List of animal IDs affected by this health event")

class HealthEventUpdate(HealthEventBase):
    # Permite que todos los campos de HealthEventBase sean opcionales para una actualización parcial
    event_type: Optional[HealthEventTypeEnumPython] = None
    event_date: Optional[datetime] = None
    description: Optional[str] = None
    product_id: Optional[uuid.UUID] = None
    quantity: Optional[Decimal] = None
    unit_id: Optional[uuid.UUID] = None
    # animal_ids no se actualizan por aquí, se manejan a través de la tabla pivot

# --- Esquema de Lectura/Respuesta (con relaciones) ---
class HealthEvent(HealthEventBase):
    id: uuid.UUID
    administered_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    # Relaciones directas (cargadas para la respuesta)
    animals_affected: List[AnimalHealthEventPivotReduced] = [] # La lista de pivotes asociados
    product: Optional[MasterDataReduced] = None
    unit: Optional[MasterDataReduced] = None
    administered_by_user: Optional[UserReduced] = None

    model_config = ConfigDict(from_attributes=True)

# Reconstruir los modelos para resolver ForwardRefs
HealthEventReduced.model_rebuild()
HealthEventReducedForPivot.model_rebuild()
HealthEvent.model_rebuild()
