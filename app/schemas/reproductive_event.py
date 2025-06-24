# app/schemas/reproductive_event.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime, date
import uuid

# Importa los ENUMS
from app.enums import ReproductiveEventTypeEnumPython, GestationDiagnosisResultEnumPython

# Importa los schemas reducidos de las entidades relacionadas
from app.schemas.user import UserReduced
from app.schemas.animal import AnimalReducedForAnimalGroup # Para animal y sire_animal

# ForwardRef para OffspringBornReduced
OffspringBornReduced = ForwardRef('OffspringBornReduced')

# --- Esquemas Reducidos para ReproductiveEvent ---
class ReproductiveEventReduced(BaseModel):
    id: uuid.UUID
    animal_id: uuid.UUID
    event_type: ReproductiveEventTypeEnumPython
    event_date: datetime
    model_config = ConfigDict(from_attributes=True)

class ReproductiveEventReducedForOffspringBorn(BaseModel): # Para uso en OffspringBornReduced
    id: uuid.UUID
    animal_id: uuid.UUID
    event_type: ReproductiveEventTypeEnumPython
    event_date: datetime
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación/Actualización ---
class ReproductiveEventBase(BaseModel):
    animal_id: uuid.UUID = Field(..., description="ID of the female animal involved in the reproductive event")
    event_type: ReproductiveEventTypeEnumPython = Field(..., description="Type of reproductive event (e.g., 'insemination', 'mating', 'gestation_diagnosis')")
    event_date: datetime = Field(default_factory=datetime.utcnow, description="Date and time the event occurred")
    description: Optional[str] = Field(None, description="Detailed description of the reproductive event")
    sire_animal_id: Optional[uuid.UUID] = Field(None, description="ID of the male animal (sire) involved, if applicable")
    gestation_diagnosis_date: Optional[datetime] = Field(None, description="Date of gestation diagnosis")
    gestation_diagnosis_result: Optional[GestationDiagnosisResultEnumPython] = Field(None, description="Result of the gestation diagnosis (e.g., 'positive', 'negative')")
    expected_offspring_date: Optional[date] = Field(None, description="Expected date of offspring birth")

    model_config = ConfigDict(from_attributes=True)

class ReproductiveEventCreate(ReproductiveEventBase):
    pass

class ReproductiveEventUpdate(ReproductiveEventBase):
    # Permite que todos los campos de ReproductiveEventBase sean opcionales para una actualización parcial
    animal_id: Optional[uuid.UUID] = None
    event_type: Optional[ReproductiveEventTypeEnumPython] = None
    event_date: Optional[datetime] = None
    description: Optional[str] = None
    sire_animal_id: Optional[uuid.UUID] = None
    gestation_diagnosis_date: Optional[datetime] = None
    gestation_diagnosis_result: Optional[GestationDiagnosisResultEnumPython] = None
    expected_offspring_date: Optional[date] = None

# --- Esquema de Lectura/Respuesta (con relaciones) ---
class ReproductiveEvent(ReproductiveEventBase):
    id: uuid.UUID
    administered_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    # Relaciones directas (cargadas para la respuesta)
    animal: Optional[AnimalReducedForAnimalGroup] = None
    sire_animal: Optional[AnimalReducedForAnimalGroup] = None
    administered_by_user: Optional[UserReduced] = None
    offspring_born_events: List[OffspringBornReduced] = [] # Lista de crías nacidas asociadas

    model_config = ConfigDict(from_attributes=True)

# Reconstruir los modelos para resolver ForwardRefs
ReproductiveEventReduced.model_rebuild()
ReproductiveEventReducedForOffspringBorn.model_rebuild()
ReproductiveEvent.model_rebuild()
