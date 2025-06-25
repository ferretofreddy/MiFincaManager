# app/schemas/offspring_born.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime
import uuid

# Importa los schemas reducidos de las entidades relacionadas
from app.schemas.user import UserReduced
from app.schemas.animal import AnimalReducedForAnimalGroup

# ForwardRef para ReproductiveEventReducedForOffspringBorn
ReproductiveEventReducedForOffspringBorn = ForwardRef('ReproductiveEventReducedForOffspringBorn')

# --- Esquemas Reducidos para OffspringBorn ---
class OffspringBornReduced(BaseModel):
    id: uuid.UUID
    reproductive_event_id: uuid.UUID
    date_of_birth: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación/Actualización ---
class OffspringBornBase(BaseModel):
    reproductive_event_id: uuid.UUID = Field(..., description="ID of the reproductive event this birth is associated with")
    offspring_animal_id: Optional[uuid.UUID] = Field(None, description="ID of the newly born animal, if registered in the system")
    date_of_birth: datetime = Field(default_factory=datetime.utcnow, description="Exact date and time of birth")
    notes: Optional[str] = Field(None, description="Any specific notes about the birth or the offspring")

    model_config = ConfigDict(from_attributes=True)

class OffspringBornCreate(OffspringBornBase):
    pass

class OffspringBornUpdate(OffspringBornBase):
    # Permite que todos los campos de OffspringBornBase sean opcionales para una actualización parcial
    reproductive_event_id: Optional[uuid.UUID] = None
    offspring_animal_id: Optional[uuid.UUID] = None
    date_of_birth: Optional[datetime] = None
    notes: Optional[str] = None

# --- Esquema de Lectura/Respuesta (con relaciones) ---
class OffspringBorn(OffspringBornBase):
    id: uuid.UUID
    born_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    # Relaciones directas (cargadas para la respuesta)
    reproductive_event: Optional[ReproductiveEventReducedForOffspringBorn] = None
    offspring_animal: Optional[AnimalReducedForAnimalGroup] = None
    born_by_user: Optional[UserReduced] = None

    model_config = ConfigDict(from_attributes=True)

