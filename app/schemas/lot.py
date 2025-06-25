# app/schemas/lot.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime
import uuid

# Importa FarmReduced de tu nuevo módulo de schemas de finca
from app.schemas.farm import FarmReduced

# Define ForwardRef para esquemas si hay circularidad

UserReduced = ForwardRef("UserReduced")
LotReduced = ForwardRef('LotReduced')
UserFarmAccessReduced = ForwardRef('UserFarmAccessReduced')
AnimalLocationHistoryReduced = ForwardRef('AnimalLocationHistoryReduced')
GrupoReduced = ForwardRef('GrupoReduced')

# --- Esquemas Reducidos
class LotReduced(BaseModel):
    id: uuid.UUID
    name: str
    farm_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación/Actualización ---
class LotBase(BaseModel):
    name: str
    description: Optional[str] = None
    area_hectares: Optional[float] = None

class LotCreate(LotBase):
    farm_id: uuid.UUID # Obligatorio para crear un lote, ya que pertenece a una finca

class LotUpdate(LotBase):
    name: Optional[str] = None
    description: Optional[str] = None
    area_hectares: Optional[float] = None
    # No permitimos cambiar farm_id después de la creación,
    # ya que un lote "pertenece" lógicamente a una única finca.
    # Si esta lógica cambia, puedes agregar farm_id: Optional[uuid.UUID] = None aquí.

# --- Esquema de Lectura/Respuesta (con relaciones) ---
class Lot(LotBase):
    id: uuid.UUID
    farm_id: uuid.UUID
    created_at: datetime # Heredado de BaseModel
    updated_at: datetime # Heredado de BaseModel

    farm: Optional[FarmReduced] = None # Usa el esquema reducido de Farm
    grupos: List["GrupoReduced"] = []
    animal_location_history: List["AnimalLocationHistoryReduced"] = [] # Se usará después de migrar AnimalLocationHistory

    model_config = ConfigDict(from_attributes=True)

