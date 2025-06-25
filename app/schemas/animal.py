# app/schemas/animal.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef # Asegúrate que ForwardRef esté aquí
from datetime import datetime, date
import uuid # Asegúrate que uuid esté aquí

# Importa los ENUMS desde donde los tengas definidos
from app.enums import (
    SexEnumPython, AnimalStatusEnumPython, AnimalOriginEnumPython, HealthEventTypeEnumPython,
    ReproductiveEventTypeEnumPython, GestationDiagnosisResultEnumPython, TransactionTypeEnumPython, ParamDataTypeEnumPython
)

# Define ForwardRef para los esquemas con los que Animal se relaciona
# y que pueden causar importación circular a nivel de módulo.
UserReduced = ForwardRef("UserReduced")
MasterDataReduced = ForwardRef("MasterDataReduced")
LotReduced = ForwardRef("LotReduced")
AnimalGroupReducedForAnimal = ForwardRef('AnimalGroupReducedForAnimal')
AnimalLocationHistoryReduced = ForwardRef('AnimalLocationHistoryReduced')
AnimalHealthEventPivot = ForwardRef('AnimalHealthEventPivot')
ReproductiveEventReduced = ForwardRef('ReproductiveEventReduced')
WeighingReduced = ForwardRef('WeighingReduced')
AnimalFeedingPivot = ForwardRef('AnimalFeedingPivot')
TransactionReduced = ForwardRef('TransactionReduced')
OffspringBornReduced = ForwardRef('OffspringBornReduced')


# --- Esquemas Reducidos para Animal ---
class AnimalReduced(BaseModel):
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
    model_config = ConfigDict(from_attributes=True)

class AnimalReducedForUser(BaseModel): # Específico para User
    id: uuid.UUID
    tag_id: str
    name: Optional[str] = None
    sex: SexEnumPython
    current_status: AnimalStatusEnumPython
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación/Actualización ---
class AnimalBase(BaseModel):
    tag_id: str = Field(..., max_length=50, description="Unique identifier for the animal (e.g., ear tag, microchip)")
    name: Optional[str] = Field(None, max_length=255, description="Name of the animal")
    sex: SexEnumPython = Field(..., description="Sex of the animal ('male', 'female', 'unknown')")
    species_id: uuid.UUID = Field(..., description="ID of the MasterData entry for the animal's species")
    breed_id: Optional[uuid.UUID] = Field(None, description="ID of the MasterData entry for the animal's breed")
    birth_date: Optional[date] = Field(None, description="Date of birth of the animal")
    current_status: AnimalStatusEnumPython = Field(..., description="Current status of the animal ('active', 'inactive', 'sold', 'deceased', etc.)")
    origin: AnimalOriginEnumPython = Field(..., description="Origin of the animal ('born_on_farm', 'purchased', 'transferred')")
    mother_id: Optional[uuid.UUID] = Field(None, description="ID of the mother animal, if known and registered")
    father_id: Optional[uuid.UUID] = Field(None, description="ID of the father animal, if known and registered")
    farm_id: uuid.UUID = Field(..., description="ID of the farm where the animal is located")
    current_lot_id: Optional[uuid.UUID] = Field(None, description="ID of the current lot/pen the animal is in")
    notes: Optional[str] = Field(None, description="Any additional notes about the animal")
    is_active: Optional[bool] = Field(True, description="Indicates if the animal record is active")

    model_config = ConfigDict(from_attributes=True)

class AnimalCreate(AnimalBase):
    pass # No necesita campos adicionales para la creación

class AnimalUpdate(AnimalBase):
    # Todos los campos son opcionales para una actualización parcial
    tag_id: Optional[str] = None
    name: Optional[str] = None
    sex: Optional[SexEnumPython] = None
    species_id: Optional[uuid.UUID] = None
    breed_id: Optional[uuid.UUID] = None
    birth_date: Optional[date] = None
    current_status: Optional[AnimalStatusEnumPython] = None
    origin: Optional[AnimalOriginEnumPython] = None
    mother_id: Optional[uuid.UUID] = None
    father_id: Optional[uuid.UUID] = None
    farm_id: Optional[uuid.UUID] = None
    current_lot_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

# --- Esquema de Lectura/Respuesta (con relaciones) ---
class Animal(AnimalBase):
    id: uuid.UUID
    created_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Relaciones directas (cargadas para la respuesta)
    created_by_user: "UserReduced"
    species: "MasterDataReduced"
    breed: Optional["MasterDataReduced"] = None
    farm: "FarmReduced"
    current_lot: Optional["LotReduced"] = None
    mother: Optional["AnimalReduced"] = None
    father: Optional["AnimalReduced"] = None

    # Relaciones con tablas de asociación y eventos
    groups_history: List["AnimalGroupReducedForAnimal"] = Field([], alias="animal_groups") # <--- USAR CADENA Y ALIAS
    locations_history: List["AnimalLocationHistoryReduced"] = Field([], alias="animal_location_history") # <--- USAR CADENA Y ALIAS
    health_events_pivot: List["AnimalHealthEventPivot"] = Field([], alias="animal_health_events") # La tabla pivote completa # <--- USAR CADENA Y ALIAS
    reproductive_events_list: List["ReproductiveEventReduced"] = Field([], alias="reproductive_events") # Ejemplo de alias # <--- USAR CADENA Y ALIAS
    sire_reproductive_events_list: List["ReproductiveEventReduced"] = Field([], alias="sire_reproductive_events") # <--- USAR CADENA Y ALIAS
    weighings_list: List["WeighingReduced"] = Field([], alias="weighings") # <--- USAR CADENA Y ALIAS
    feedings_pivot: List["AnimalFeedingPivot"] = Field([], alias="animal_feedings") # La tabla pivote completa # <--- USAR CADENA Y ALIAS
    transactions_list: List["TransactionReduced"] = Field([], alias="transactions") # <--- USAR CADENA Y ALIAS
    offspring_born_events_list: List["OffspringBornReduced"] = Field([], alias="offspring_born_events") # <--- USAR CADENA Y ALIAS

    model_config = ConfigDict(from_attributes=True)

