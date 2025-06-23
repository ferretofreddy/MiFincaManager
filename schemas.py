# schemas.py
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime, date
import uuid

# Importa los ENUMS de Python directamente desde el nuevo archivo app_enums
from app_enums import (
    SexEnumPython, AnimalStatusEnumPython, AnimalOriginEnumPython, HealthEventTypeEnumPython,
    ReproductiveEventTypeEnumPython, GestationDiagnosisResultEnumPython, TransactionTypeEnumPython, ParamDataTypeEnumPython
)

# --- Nuevos Esquemas de Token ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[uuid.UUID] = None

# --- Esquemas Reducidos para Romper Ciclos de Recursión ---
# Estas versiones solo incluyen los campos básicos para evitar bucles infinitos
class UserReduced(BaseModel):
    id: uuid.UUID
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class FarmReduced(BaseModel):
    id: uuid.UUID
    name: str
    location: Optional[str] = None
    owner_user_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class LotReduced(BaseModel):
    id: uuid.UUID
    name: str
    farm_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class MasterDataReduced(BaseModel):
    id: uuid.UUID
    category: str
    name: str
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class GrupoReduced(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    purpose_id: Optional[uuid.UUID] = None
    created_by_user_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


# Definición ForwardRef para Animal antes de AnimalGroupReducedForAnimal
Animal = ForwardRef('Animal')

class AnimalReducedForAnimalGroup(BaseModel):
    """Esquema reducido de Animal para usar dentro de AnimalGroup para evitar recursión."""
    id: uuid.UUID
    tag_id: str
    name: Optional[str] = None
    sex: SexEnumPython
    current_status: AnimalStatusEnumPython
    owner_user_id: uuid.UUID
    current_lot_id: Optional[uuid.UUID] = None
    model_config = ConfigDict(from_attributes=True)

class GrupoReducedForAnimalGroup(BaseModel):
    """Esquema reducido de Grupo para usar dentro de AnimalGroup para evitar recursión."""
    id: uuid.UUID
    name: str
    model_config = ConfigDict(from_attributes=True)

class AnimalGroupReducedForAnimal(BaseModel):
    """Esquema reducido de AnimalGroup para usar dentro de Animal para evitar recursión."""
    animal_id: uuid.UUID
    grupo_id: uuid.UUID
    assigned_date: Optional[date] = None
    removed_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- NUEVO: Esquema reducido para HealthEvent (DEFINIDO COMO CLASE AHORA) ---
# Este esquema es el que se referenciará para romper ciclos.
class HealthEventReduced(BaseModel):
    """Esquema reducido de HealthEvent para usar dentro de AnimalHealthEventPivot."""
    id: uuid.UUID
    event_type: HealthEventTypeEnumPython
    event_date: date
    model_config = ConfigDict(from_attributes=True)
# -------------------------------------------------------------------------


# --- Esquemas Base (mantenerlos sencillos, sin relaciones cargadas) ---
class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None
    module_id: Optional[uuid.UUID] = None

class FarmBase(BaseModel):
    name: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    area_hectares: Optional[float] = None
    contact_info: Optional[str] = None

class LotBase(BaseModel):
    name: str
    description: Optional[str] = None

class MasterDataBase(BaseModel):
    category: str
    name: str
    description: Optional[str] = None
    properties: Optional[dict] = None
    is_active: Optional[bool] = True

class AnimalBase(BaseModel):
    tag_id: str = Field(..., max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    species_id: Optional[uuid.UUID] = None
    breed_id: Optional[uuid.UUID] = None
    sex: SexEnumPython
    date_of_birth: Optional[date] = None
    current_status: AnimalStatusEnumPython
    origin: AnimalOriginEnumPython
    mother_animal_id: Optional[uuid.UUID] = None
    father_animal_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    photo_url: Optional[str] = Field(None, max_length=255)
    current_lot_id: Optional[uuid.UUID] = None
    model_config = ConfigDict(from_attributes=True)

class GrupoBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    purpose_id: Optional[uuid.UUID] = None
    model_config = ConfigDict(from_attributes=True)

class AnimalGroupBase(BaseModel):
    animal_id: uuid.UUID
    grupo_id: uuid.UUID
    assigned_date: Optional[date] = None
    removed_date: Optional[date] = None
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# --- HealthEvent Schemas ---
class HealthEventBase(BaseModel):
    event_type: HealthEventTypeEnumPython
    event_date: date
    product_id: Optional[uuid.UUID] = None
    dosage: Optional[str] = None
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class HealthEventCreate(HealthEventBase):
    animal_ids: List[uuid.UUID] = Field(..., description="List of animal IDs affected by this health event")

class HealthEventUpdate(HealthEventBase):
    event_type: Optional[HealthEventTypeEnumPython] = None
    event_date: Optional[date] = None

# --- NUEVOS: Esquemas para ReproductiveEvent ---
class ReproductiveEventBase(BaseModel):
    animal_id: uuid.UUID
    event_type: ReproductiveEventTypeEnumPython
    event_date: date
    sire_animal_id: Optional[uuid.UUID] = None
    gestation_diagnosis_result: Optional[GestationDiagnosisResultEnumPython] = None
    expected_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None
    number_of_offspring: Optional[int] = None
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ReproductiveEventCreate(ReproductiveEventBase):
    pass

class ReproductiveEventUpdate(ReproductiveEventBase):
    animal_id: Optional[uuid.UUID] = None
    event_type: Optional[ReproductiveEventTypeEnumPython] = None
    event_date: Optional[date] = None

# --- NUEVOS: Esquemas para OffspringBorn ---
class OffspringBornBase(BaseModel):
    reproductive_event_id: uuid.UUID
    offspring_animal_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class OffspringBornCreate(OffspringBornBase):
    pass

class OffspringBornUpdate(OffspringBornBase):
    reproductive_event_id: Optional[uuid.UUID] = None
    offspring_animal_id: Optional[uuid.UUID] = None

# --- NUEVOS: Esquemas para Weighing ---
class WeighingBase(BaseModel):
    animal_id: uuid.UUID
    weighing_date: date
    weight_kg: float
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class WeighingCreate(WeighingBase):
    pass

class WeighingUpdate(WeighingBase):
    animal_id: Optional[uuid.UUID] = None
    weighing_date: Optional[date] = None
    weight_kg: Optional[float] = None

# --- NUEVOS: Esquemas para Feeding ---
class FeedingBase(BaseModel):
    feeding_date: date
    feed_type_id: uuid.UUID
    quantity_kg: float
    supplement_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class FeedingCreate(FeedingBase):
    animal_ids: List[uuid.UUID] = []

class FeedingUpdate(FeedingBase):
    feeding_date: Optional[date] = None
    feed_type_id: Optional[uuid.UUID] = None

# --- NUEVOS: Esquemas para AnimalFeedingPivot ---
class AnimalFeedingPivotBase(BaseModel):
    feeding_id: uuid.UUID
    animal_id: uuid.UUID
    created_at: Optional[datetime] = None # Hacer opcional ya que la DB lo genera

    model_config = ConfigDict(from_attributes=True)

# --- NUEVOS: Esquemas para Transaction ---
class TransactionBase(BaseModel):
    transaction_type: TransactionTypeEnumPython
    transaction_date: date
    animal_id: uuid.UUID
    from_farm_id: Optional[uuid.UUID] = None
    to_farm_id: Optional[uuid.UUID] = None
    from_owner_user_id: uuid.UUID
    to_owner_user_id: Optional[uuid.UUID] = None
    price_value: Optional[float] = None
    reason_for_movement: Optional[str] = None
    transport_info: Optional[str] = None
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(TransactionBase):
    transaction_type: Optional[TransactionTypeEnumPython] = None
    transaction_date: Optional[date] = None

# --- NUEVOS: Esquemas para ConfigurationParameter ---
class ConfigurationParameterBase(BaseModel):
    parameter_name: str
    parameter_value: str
    data_type: ParamDataTypeEnumPython
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ConfigurationParameterCreate(ConfigurationParameterBase):
    pass

class ConfigurationParameterUpdate(ConfigurationParameterBase):
    parameter_value: Optional[str] = None
    data_type: Optional[ParamDataTypeEnumPython] = None

# --- Esquemas de Creación ---
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class RoleCreate(RoleBase):
    pass

class PermissionCreate(PermissionBase):
    pass

class FarmCreate(FarmBase):
    pass

class LotCreate(LotBase):
    farm_id: uuid.UUID

class MasterDataCreate(MasterDataBase):
    pass

class AnimalCreate(AnimalBase):
    pass

class GrupoCreate(GrupoBase):
    pass

class AnimalGroupCreate(AnimalGroupBase):
    pass

# --- Esquemas de Actualización ---
class UserUpdate(UserBase):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)

class RoleUpdate(RoleBase):
    name: Optional[str] = None
    description: Optional[str] = None

class PermissionUpdate(PermissionBase):
    name: Optional[str] = None
    description: Optional[str] = None
    module_id: Optional[uuid.UUID] = None

class FarmUpdate(FarmBase):
    name: Optional[str] = None

class LotUpdate(LotBase):
    name: Optional[str] = None
    farm_id: Optional[uuid.UUID] = None

class MasterDataUpdate(MasterDataBase):
    category: Optional[str] = None
    name: Optional[str] = None

class AnimalUpdate(AnimalBase):
    tag_id: Optional[str] = Field(None, max_length=50)
    sex: Optional[SexEnumPython] = None
    current_status: Optional[AnimalStatusEnumPython] = None
    origin: Optional[AnimalOriginEnumPython] = None

class GrupoUpdate(GrupoBase):
    name: Optional[str] = None
    purpose_id: Optional[uuid.UUID] = None

class AnimalGroupUpdate(AnimalGroupBase):
    animal_id: Optional[uuid.UUID] = None
    grupo_id: Optional[uuid.UUID] = None
    assigned_date: Optional[date] = None

# --- Esquemas de Lectura/Respuesta (con relaciones) ---
class User(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class Role(RoleBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class Permission(PermissionBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class Farm(FarmBase):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    owner_user: Optional[UserReduced] = None
    model_config = ConfigDict(from_attributes=True)

class Lot(LotBase):
    id: uuid.UUID
    farm_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    farm: Optional[FarmReduced] = None
    model_config = ConfigDict(from_attributes=True)

class MasterData(MasterDataBase):
    id: uuid.UUID
    created_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    created_by_user: Optional[UserReduced] = None
    model_config = ConfigDict(from_attributes=True)

class Grupo(GrupoBase):
    id: uuid.UUID
    created_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    purpose: Optional[MasterDataReduced] = None
    created_by_user: Optional[UserReduced] = None
    model_config = ConfigDict(from_attributes=True)

class AnimalGroup(AnimalGroupBase):
    created_at: datetime
    animal: Optional[AnimalReducedForAnimalGroup] = None
    grupo: Optional[GrupoReducedForAnimalGroup] = None
    model_config = ConfigDict(from_attributes=True)

# Esquema para la tabla pivote de AnimalHealthEventPivot
class AnimalHealthEventPivot(BaseModel):
    health_event_id: uuid.UUID
    animal_id: uuid.UUID
    created_at: datetime

    # ¡IMPORTANTE: Usar la versión reducida de HealthEvent para evitar la recursión!
    # Ahora que HealthEventReduced está definido como clase, se usa directamente.
    health_event: Optional[HealthEventReduced] = None
    animal: Optional[AnimalReducedForAnimalGroup] = None

    model_config = ConfigDict(from_attributes=True)

class HealthEvent(HealthEventBase):
    id: uuid.UUID
    administered_by_user_id: Optional[uuid.UUID] = None
    created_at: datetime

    product: Optional[MasterDataReduced] = None
    administered_by_user: Optional[UserReduced] = None
    animals_affected: List[AnimalHealthEventPivot] = Field([], alias="animals_affected")

    model_config = ConfigDict(from_attributes=True)

class ReproductiveEvent(ReproductiveEventBase):
    id: uuid.UUID
    created_at: datetime
    animal_obj: Optional[AnimalReducedForAnimalGroup] = Field(None, alias="animal")
    sire_animal_obj: Optional[AnimalReducedForAnimalGroup] = Field(None, alias="sire_animal")
    model_config = ConfigDict(from_attributes=True)

class OffspringBorn(OffspringBornBase):
    created_at: datetime
    reproductive_event_obj: Optional[ReproductiveEvent] = Field(None, alias="reproductive_event")
    offspring_animal_obj: Optional[AnimalReducedForAnimalGroup] = Field(None, alias="offspring_animal")
    model_config = ConfigDict(from_attributes=True)

class Weighing(WeighingBase):
    id: uuid.UUID
    created_at: datetime
    animal_obj: Optional[AnimalReducedForAnimalGroup] = Field(None, alias="animal")
    model_config = ConfigDict(from_attributes=True)

class Feeding(FeedingBase):
    id: uuid.UUID
    created_at: datetime
    feed_type_obj: Optional[MasterDataReduced] = Field(None, alias="feed_type")
    supplement_obj: Optional[MasterDataReduced] = Field(None, alias="supplement")
    administered_by_user_obj: Optional[UserReduced] = Field(None, alias="administered_by_user")
    model_config = ConfigDict(from_attributes=True)

class AnimalFeedingPivot(AnimalFeedingPivotBase):
    created_at: datetime
    feeding_obj: Optional[Feeding] = Field(None, alias="feeding")
    animal_obj: Optional[AnimalReducedForAnimalGroup] = Field(None, alias="animal")
    model_config = ConfigDict(from_attributes=True)

class Transaction(TransactionBase):
    id: uuid.UUID
    created_at: datetime
    animal_obj: Optional[AnimalReducedForAnimalGroup] = Field(None, alias="animal")
    from_farm_obj: Optional[FarmReduced] = Field(None, alias="from_farm")
    to_farm_obj: Optional[FarmReduced] = Field(None, alias="to_farm")
    from_owner_user_obj: Optional[UserReduced] = Field(None, alias="from_owner_user")
    to_owner_user_obj: Optional[UserReduced] = Field(None, alias="to_owner_user")
    model_config = ConfigDict(from_attributes=True)

class ConfigurationParameter(ConfigurationParameterBase):
    id: uuid.UUID
    updated_at: datetime
    last_updated_by_user_obj: Optional[UserReduced] = Field(None, alias="last_updated_by_user")
    model_config = ConfigDict(from_attributes=True)

class Animal(AnimalBase):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    owner_user: Optional[UserReduced] = None
    species: Optional[MasterDataReduced] = None
    breed: Optional[MasterDataReduced] = None
    current_lot: Optional[LotReduced] = None
    groups_history: List[AnimalGroupReducedForAnimal] = []
    locations_history: List['AnimalLocationHistory'] = []
    health_events: List['AnimalHealthEventPivot'] = Field([], alias="health_events_pivot")
    reproductive_events_list: List[ReproductiveEvent] = Field([], alias="reproductive_events")
    sire_reproductive_events_list: List[ReproductiveEvent] = Field([], alias="sire_reproductive_events")
    weighings_list: List[Weighing] = Field([], alias="weighings")
    feedings_list: List['AnimalFeedingPivot'] = Field([], alias="feedings_pivot")
    transactions_list: List[Transaction] = Field([], alias="transactions")
    offspring_born_events_list: List[OffspringBorn] = Field([], alias="offspring_born_events")
    model_config = ConfigDict(from_attributes=True)

class AnimalLocationHistory(BaseModel):
    id: uuid.UUID
    animal_id: uuid.UUID
    farm_id: uuid.UUID
    entry_date: date
    exit_date: Optional[date] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    animal: Optional[AnimalReducedForAnimalGroup] = None
    farm: Optional[FarmReduced] = None
    model_config = ConfigDict(from_attributes=True)

# Definición forward-ref para resolver dependencias circulares
# ¡Orden crucial para model_rebuild()! De los que menos dependen a los que más.
UserReduced.model_rebuild()
FarmReduced.model_rebuild()
LotReduced.model_rebuild()
MasterDataReduced.model_rebuild()
GrupoReduced.model_rebuild()
AnimalReducedForAnimalGroup.model_rebuild()
GrupoReducedForAnimalGroup.model_rebuild()
AnimalGroupReducedForAnimal.model_rebuild()

# ¡Ahora llamamos a model_rebuild en la CLASE real HealthEventReduced!
HealthEventReduced.model_rebuild()

AnimalHealthEventPivot.model_rebuild()
AnimalLocationHistory.model_rebuild()

User.model_rebuild()
Role.model_rebuild()
Permission.model_rebuild()
MasterData.model_rebuild()
Farm.model_rebuild()
Lot.model_rebuild()
Grupo.model_rebuild()
AnimalGroup.model_rebuild()
HealthEvent.model_rebuild()
ReproductiveEvent.model_rebuild()
OffspringBorn.model_rebuild()
Weighing.model_rebuild()
Feeding.model_rebuild()
AnimalFeedingPivot.model_rebuild()
Transaction.model_rebuild()
ConfigurationParameter.model_rebuild()
Animal.model_rebuild()
