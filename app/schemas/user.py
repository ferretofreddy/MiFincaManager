# app/schemas/user.py
from typing import Optional, List, ForwardRef
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict
import uuid

# Importa otros esquemas o define ForwardRef para evitar circularidad
FarmReduced = ForwardRef("FarmReduced")
AnimalReducedForUser = ForwardRef("AnimalReducedForUser")
MasterDataReduced = ForwardRef("MasterDataReduced")
HealthEventReduced = ForwardRef("HealthEventReduced")
ReproductiveEventReduced = ForwardRef("ReproductiveEventReduced")
OffspringBornReduced = ForwardRef("OffspringBornReduced")
WeighingReduced = ForwardRef("WeighingReduced")
FeedingReduced = ForwardRef("FeedingReduced")
TransactionReduced = ForwardRef("TransactionReduced")
BatchReduced = ForwardRef("BatchReduced")
GrupoReduced = ForwardRef("GrupoReduced")
AnimalGroupReduced = ForwardRef("AnimalGroupReduced")
AnimalLocationHistoryReduced = ForwardRef("AnimalLocationHistoryReduced")
ProductReduced = ForwardRef("ProductReduced")
RoleReduced = ForwardRef("RoleReduced")
UserRole = ForwardRef("UserRole")
UserFarmAccess = ForwardRef("UserFarmAccess")

class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    # === ¡CAMBIO CLAVE AQUÍ! Ahora el esquema espera 'password' en texto plano ===
    password: str = Field(..., min_length=8, description="Password for the user")
    is_superuser: bool = False
    is_active: bool = True

class UserUpdate(UserBase):
    # Para actualizaciones, todos los campos son opcionales
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, description="New password for the user (optional)")
    is_superuser: Optional[bool] = None
    is_active: Optional[bool] = None
    # Otros campos que puedan ser actualizables
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None

# Esquemas de Lectura/Respuesta (con relaciones)
class UserReduced(UserBase):
    id: uuid.UUID
    is_active: bool
    is_superuser: bool

class User(UserBase):
    id: uuid.UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    # hashed_password: str # No exponer el hash en la respuesta si no es necesario

    farms_owned: List[FarmReduced] = Field(default_factory=list)
    animals_owned: List[AnimalReducedForUser] = Field(default_factory=list)
    farm_accesses: List["UserFarmAccess"] = Field(default_factory=list)
    accesses_assigned: List["UserFarmAccess"] = Field(default_factory=list)
    master_data_created: List[MasterDataReduced] = Field(default_factory=list)
    health_events_administered: List[HealthEventReduced] = Field(default_factory=list)
    reproductive_events_administered: List[ReproductiveEventReduced] = Field(default_factory=list)
    offspring_born: List[OffspringBornReduced] = Field(default_factory=list)
    weighings_recorded: List[WeighingReduced] = Field(default_factory=list)
    feedings_recorded: List[FeedingReduced] = Field(default_factory=list)
    transactions_recorded: List[TransactionReduced] = Field(default_factory=list)
    batches_created: List[BatchReduced] = Field(default_factory=list)
    grupos_created: List[GrupoReduced] = Field(default_factory=list)
    animal_groups_created: List[AnimalGroupReduced] = Field(default_factory=list)
    animal_location_history_created: List[AnimalLocationHistoryReduced] = Field(default_factory=list)
    products_created: List[ProductReduced] = Field(default_factory=list)

    roles_assigned_to_user: List[RoleReduced] = Field(default_factory=list)
    user_roles_associations: List["UserRole"] = Field(default_factory=list)
    assigned_roles: List["UserRole"] = Field(default_factory=list)
    
    configuration_parameters_created: List["ConfigurationParameter"] = Field(default_factory=list)

