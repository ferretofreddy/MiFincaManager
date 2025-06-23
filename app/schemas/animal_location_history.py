# app/schemas/animal_location_history.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime
import uuid

# Importa los schemas reducidos de las entidades relacionadas
from app.schemas.animal import AnimalReduced, AnimalReducedForAnimalGroup # Revisa cuál AnimalReduced es más apropiado aquí
from app.schemas.lot import LotReduced
from app.schemas.user import UserReduced

# --- Esquemas Reducidos para AnimalLocationHistory ---
class AnimalLocationHistoryReduced(BaseModel):
    id: uuid.UUID # El ID de la BaseModel
    animal_id: uuid.UUID
    lot_id: uuid.UUID
    entry_date: datetime
    departure_date: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class AnimalLocationHistoryReducedForAnimal(BaseModel): # Para ser usado cuando se consulta un Animal
    id: uuid.UUID
    lot_id: uuid.UUID
    entry_date: datetime
    departure_date: Optional[datetime] = None
    lot: Optional[LotReduced] = None # Para evitar recursión
    model_config = ConfigDict(from_attributes=True)

class AnimalLocationHistoryReducedForLot(BaseModel): # Para ser usado cuando se consulta un Lote
    id: uuid.UUID
    animal_id: uuid.UUID
    entry_date: datetime
    departure_date: Optional[datetime] = None
    animal: Optional[AnimalReducedForAnimalGroup] = None # Para evitar recursión, o AnimalReduced si es suficiente
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación/Actualización ---
class AnimalLocationHistoryBase(BaseModel):
    animal_id: uuid.UUID = Field(..., description="ID of the animal whose location is being recorded")
    lot_id: uuid.UUID = Field(..., description="ID of the lot where the animal is located")
    entry_date: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the animal entered the lot")
    departure_date: Optional[datetime] = Field(None, description="Timestamp when the animal departed the lot (if applicable)")

    model_config = ConfigDict(from_attributes=True)

class AnimalLocationHistoryCreate(AnimalLocationHistoryBase):
    pass

class AnimalLocationHistoryUpdate(BaseModel):
    # Permite actualizar solo departure_date o cualquier otro campo modificable
    departure_date: Optional[datetime] = Field(None, description="Timestamp when the animal departed the lot")
    # Puedes añadir otros campos si son actualizables
    model_config = ConfigDict(from_attributes=True)

# --- Esquema de Lectura/Respuesta (con relaciones) ---
class AnimalLocationHistory(AnimalLocationHistoryBase):
    id: uuid.UUID # El ID de la BaseModel
    created_by_user_id: uuid.UUID
    created_at: datetime # Heredado de BaseModel
    updated_at: datetime # Heredado de BaseModel

    # Relaciones directas (cargadas para la respuesta)
    animal: Optional[AnimalReducedForAnimalGroup] = None # Usar el schema reducido apropiado
    lot: Optional[LotReduced] = None                  # Usar el schema reducido
    created_by_user: Optional[UserReduced] = None        # Usar el schema reducido

    model_config = ConfigDict(from_attributes=True)

# Reconstruir los modelos para resolver ForwardRefs
AnimalLocationHistoryReduced.model_rebuild()
AnimalLocationHistoryReducedForAnimal.model_rebuild()
AnimalLocationHistoryReducedForLot.model_rebuild()
AnimalLocationHistory.model_rebuild()
