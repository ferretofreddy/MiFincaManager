# app/schemas/animal.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime, date
import uuid

# Importa los ENUMS desde donde los tengas definidos
# Asumo que tienes un archivo app_enums.py en la raíz del proyecto.
# Si no, deberías moverlos a app/core/enums.py por ejemplo.
from app_enums import (
    SexEnumPython, AnimalStatusEnumPython, AnimalOriginEnumPython, HealthEventTypeEnumPython,
    ReproductiveEventTypeEnumPython, GestationDiagnosisResultEnumPython, TransactionTypeEnumPython, ParamDataTypeEnumPython
)

# Importa los schemas reducidos de las entidades relacionadas
from app.schemas.user import UserReduced
from app.schemas.master_data import MasterDataReduced
from app.schemas.lot import LotReduced

# --- Esquemas Reducidos para Animal ---
# Para usar en relaciones inversas o cuando solo se necesita información básica del animal
class AnimalReduced(BaseModel): # Un esquema reducido general para Animal
    id: uuid.UUID
    tag_id: str
    name: Optional[str] = None
    sex: SexEnumPython
    current_status: AnimalStatusEnumPython
    model_config = ConfigDict(from_attributes=True)

class AnimalReducedForAnimalGroup(BaseModel): # Específico para AnimalGroup
    id: uuid.UUID
    tag_id: str
    name: Optional[str] = None
    sex: SexEnumPython
    current_status: AnimalStatusEnumPython
    owner_user_id: uuid.UUID
    current_lot_id: Optional[uuid.UUID] = None
    model_config = ConfigDict(from_attributes=True)

class AnimalReducedForUser(BaseModel): # Específico para User
    id: uuid.UUID
    tag_id: str
    name: Optional[str] = None
    sex: SexEnumPython
    model_config = ConfigDict(from_attributes=True)

# Puedes tener otros AnimalReduced según la necesidad (ej. ForHealthEvent, ForFeeding)
# class AnimalReducedForHealthEvent(BaseModel):
#     id: uuid.UUID
#     tag_id: str
#     name: Optional[str] = None
#     model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación/Actualización ---
class AnimalBase(BaseModel):
    tag_id: str = Field(..., max_length=50, description="Unique identifier for the animal (e.g., ear tag, microchip)")
    name: Optional[str] = Field(None, max_length=100, description="Name of the animal")
    species_id: Optional[uuid.UUID] = Field(None, description="ID of the MasterData entry for species")
    breed_id: Optional[uuid.UUID] = Field(None, description="ID of the MasterData entry for breed")
    sex: SexEnumPython = Field(..., description="Sex of the animal (Male, Female, Unknown)")
    date_of_birth: Optional[date] = Field(None, description="Date of birth of the animal")
    current_status: AnimalStatusEnumPython = Field(..., description="Current status of the animal (e.g., Active, Sold, Deceased)")
    origin: AnimalOriginEnumPython = Field(..., description="Origin of the animal (e.g., Born in farm, Purchased)")
    mother_animal_id: Optional[uuid.UUID] = Field(None, description="ID of the mother animal (self-referencing)")
    father_animal_id: Optional[uuid.UUID] = Field(None, description="ID of the father animal (self-referencing)")
    description: Optional[str] = None
    photo_url: Optional[str] = Field(None, max_length=255)
    current_lot_id: Optional[uuid.UUID] = Field(None, description="ID of the current lot where the animal is located")

    model_config = ConfigDict(from_attributes=True)

class AnimalCreate(AnimalBase):
    pass # No necesita campos adicionales para la creación

class AnimalUpdate(AnimalBase):
    # Todos los campos son opcionales para la actualización
    tag_id: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    species_id: Optional[uuid.UUID] = None
    breed_id: Optional[uuid.UUID] = None
    sex: Optional[SexEnumPython] = None
    date_of_birth: Optional[date] = None
    current_status: Optional[AnimalStatusEnumPython] = None
    origin: Optional[AnimalOriginEnumPython] = None
    mother_animal_id: Optional[uuid.UUID] = None
    father_animal_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    photo_url: Optional[str] = Field(None, max_length=255)
    current_lot_id: Optional[uuid.UUID] = None

# --- Esquema de Lectura/Respuesta (con relaciones) ---
class Animal(AnimalBase):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    created_at: datetime # Heredado de BaseModel
    updated_at: datetime # Heredado de BaseModel

    # Relaciones directas (cargadas para la respuesta)
    owner_user: Optional[UserReduced] = None
    species: Optional[MasterDataReduced] = None
    breed: Optional[MasterDataReduced] = None
    current_lot: Optional[LotReduced] = None
    
    # Relaciones auto-referenciadas
    mother: Optional[AnimalReduced] = None # Usa un AnimalReduced para evitar recursión infinita
    father: Optional[AnimalReduced] = None # Usa un AnimalReduced para evitar recursión infinita

    # Relaciones con tablas de asociación y eventos
    # Usamos ForwardRef para los schemas que aún no hemos migrado/definido
    groups_history: List[ForwardRef('AnimalGroupReducedForAnimal')] = []
    locations_history: List[ForwardRef('AnimalLocationHistoryReduced')] = []
    health_events_pivot: List[ForwardRef('AnimalHealthEventPivot')] = [] # La tabla pivote completa
    reproductive_events_list: List[ForwardRef('ReproductiveEventReduced')] = Field([], alias="reproductive_events") # Ejemplo de alias
    sire_reproductive_events_list: List[ForwardRef('ReproductiveEventReduced')] = Field([], alias="sire_reproductive_events")
    weighings_list: List[ForwardRef('WeighingReduced')] = Field([], alias="weighings")
    feedings_pivot: List[ForwardRef('AnimalFeedingPivot')] = [] # La tabla pivote completa
    transactions_list: List[ForwardRef('TransactionReduced')] = Field([], alias="transactions")
    offspring_born_events_list: List[ForwardRef('OffspringBornReduced')] = Field([], alias="offspring_born_events")

    model_config = ConfigDict(from_attributes=True)

# Reconstruir los modelos para resolver ForwardRefs
AnimalReduced.model_rebuild()
AnimalReducedForAnimalGroup.model_rebuild()
AnimalReducedForUser.model_rebuild()
Animal.model_rebuild() # Asegúrate de que este sea el último rebuild para Animal
