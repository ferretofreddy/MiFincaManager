# app/schemas/user.py
from typing import Optional, List, ForwardRef
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict

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

class UserBase(BaseModel):
    # ... (tus campos existentes) ...
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    hashed_password: str # Contraseña ya hasheada (desde el backend)

class UserUpdate(UserBase):
    email: Optional[EmailStr] = None
    hashed_password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

class UserReduced(BaseModel):
    id: uuid.UUID
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class User(UserBase):
    id: uuid.UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Relaciones de Pydantic - USANDO REFERENCIAS DE STRING O FORWARDREF
    farms_owned: List["FarmReduced"] = Field(default_factory=list)
    animals_owned: List["AnimalReducedForUser"] = Field(default_factory=list)
    farm_accesses: List["UserFarmAccess"] = Field(default_factory=list)
    accesses_assigned: List["UserFarmAccess"] = Field(default_factory=list)
    master_data_created: List["MasterDataReduced"] = Field(default_factory=list)
    health_events_administered: List["HealthEventReduced"] = Field(default_factory=list)
    reproductive_events_administered: List["ReproductiveEventReduced"] = Field(default_factory=list)
    offspring_born: List["OffspringBornReduced"] = Field(default_factory=list)
    weighings_recorded: List["WeighingReduced"] = Field(default_factory=list)
    feedings_recorded: List["FeedingReduced"] = Field(default_factory=list)
    transactions_recorded: List["TransactionReduced"] = Field(default_factory=list)
    batches_created: List["BatchReduced"] = Field(default_factory=list)
    grupos_created: List["GrupoReduced"] = Field(default_factory=list)
    animal_groups_created: List["AnimalGroupReduced"] = Field(default_factory=list)
    animal_location_history_created: List["AnimalLocationHistoryReduced"] = Field(default_factory=list)
    products_created: List["ProductReduced"] = Field(default_factory=list)

    # Relaciones de seguridad (usando el esquema reducido de Role)
    user_roles_associations: List["UserRole"] = Field(default_factory=list)
    assigned_roles: List["UserRole"] = Field(default_factory=list)
    roles: List["RoleReduced"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

# Reconstruir los modelos para resolver ForwardRefs
UserReduced.model_rebuild()
User.model_rebuild()
