# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime
import uuid

# Importa los ENUMS si es necesario para los schemas de usuario.
# Si los enums están en un archivo app_enums.py en la raíz, entonces:
# from app_enums import SexEnumPython, ... (solo los que necesites aquí)

# Aquí puedes importar los schemas reducidos que uses en las relaciones de User.
# Por ahora, solo UserReduced, pero luego necesitarás FarmReduced, Role, etc.
# Ejemplo:
# from app.schemas.farm import FarmReduced
# from app.schemas.role import Role # Si Role tiene su propio archivo

# --- Esquemas Reducidos para Romper Ciclos de Recursión (UserReduced se queda aquí) ---
class UserReduced(BaseModel):
    id: uuid.UUID
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas de Usuario ---
class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

class User(UserBase):
    id: uuid.UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    # Relaciones con otros Schemas - DEBERÁS ADAPTAR ESTO
    # Cuando migres los otros schemas (Farm, Animal, Role, etc.),
    # deberás importarlos aquí. Por ahora, las dejaremos como ForwardRef.
    # Por ejemplo, si tienes app/schemas/farm.py con FarmReduced:
    # from app.schemas.farm import FarmReduced

    # Estas líneas pueden dar errores de "name 'Role' is not defined"
    # hasta que migremos esos schemas a sus propios archivos
    # y los importemos correctamente.
    # Por ahora, para que Pydantic 2.x compile, las dejamos como ForwardRef.
    # Cuando migres Role, Farm, etc., deberás:
    # 1. Mover sus definiciones a app/schemas/role.py, app/schemas/farm.py, etc.
    # 2. Importarlos aquí: from app.schemas.role import Role
    # 3. Quitar el ' alrededor del nombre: roles: List[Role] = []
    roles: List[ForwardRef('Role')] = []
    farms_owned: List[ForwardRef('FarmReduced')] = []
    animals_owned: List[ForwardRef('AnimalReducedForUser')] = []
    farm_accesses: List[ForwardRef('UserFarmAccess')] = []
    accesses_assigned: List[ForwardRef('UserFarmAccess')] = []
    master_data_created: List[ForwardRef('MasterDataReduced')] = []
    health_events_administered: List[ForwardRef('HealthEventReducedForUser')] = []
    reproductive_events_administered: List[ForwardRef('ReproductiveEventReducedForUser')] = []
    offspring_born: List[ForwardRef('OffspringBornReducedForUser')] = []
    weighings_recorded: List[ForwardRef('WeighingReducedForUser')] = []
    feedings_recorded: List[ForwardRef('FeedingReducedForUser')] = []
    batches_created: List[ForwardRef('BatchReducedForUser')] = []
    transaction_records_created: List[ForwardRef('TransactionRecordReducedForUser')] = []
    permissions_assigned: List[ForwardRef('UserPermission')] = []


    model_config = ConfigDict(from_attributes=True)

# Al final del archivo, después de todas las definiciones de schemas
# relevantes para usuario y sus relaciones, ejecuta model_rebuild()
# para resolver los ForwardRefs.
UserReduced.model_rebuild()
User.model_rebuild()
