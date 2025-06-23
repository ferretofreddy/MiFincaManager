# app/schemas/farm.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime
import uuid

# Importa el UserReduced de tu nuevo módulo de schemas de usuario
from app.schemas.user import UserReduced

# --- Esquemas Reducidos (FarmReduced se queda aquí) ---
class FarmReduced(BaseModel):
    id: uuid.UUID
    name: str
    location: Optional[str] = None
    owner_user_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación/Actualización ---
class FarmBase(BaseModel):
    name: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    area_hectares: Optional[float] = None
    contact_info: Optional[str] = None

class FarmCreate(FarmBase):
    pass # No necesita campos adicionales para la creación

class FarmUpdate(FarmBase):
    name: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    area_hectares: Optional[float] = None
    contact_info: Optional[str] = None

# --- Esquema de Lectura/Respuesta (con relaciones) ---
class Farm(FarmBase):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    created_at: datetime # Heredado de BaseModel
    updated_at: datetime # Heredado de BaseModel

    owner_user: Optional[UserReduced] = None # Usa el esquema reducido de User

    # Aquí irían las relaciones a LotReduced, UserFarmAccessReduced, etc.
    # Por ahora las dejamos como ForwardRef, pero deberás migrarlas y luego quitarlas.
    lots: List[ForwardRef('LotReduced')] = []
    user_accesses: List[ForwardRef('UserFarmAccessReduced')] = []
    animal_locations: List[ForwardRef('AnimalLocationHistoryReduced')] = []

    model_config = ConfigDict(from_attributes=True)

# Reconstruir los modelos para resolver ForwardRefs (si los hay)
# Solo si los esquemas reducidos no tienen ForwardRefs propios no necesitan rebuild
FarmReduced.model_rebuild()
Farm.model_rebuild()
