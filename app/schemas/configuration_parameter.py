# app/schemas/configuration_parameter.py
import uuid
from datetime import datetime
from typing import Optional, Any, Dict, ForwardRef
from pydantic import BaseModel, Field, ConfigDict

# En este caso, MasterDataReduced es una dependencia.
MasterDataReduced = ForwardRef('MasterDataReduced') # Para el tipo de dato del parámetro
UserReduced = ForwardRef('UserReduced') # Para el usuario que creó/modificó


# --- Esquemas Reducidos para ConfigurationParameter ---
class ConfigurationParameterReduced(BaseModel):
    id: uuid.UUID
    name: str
    value: str # Almacenar el valor como string para flexibilidad
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación/Actualización ---
class ConfigurationParameterBase(BaseModel):
    name: str = Field(..., description="Unique name of the configuration parameter (e.g., 'MAX_ANIMALS_PER_FARM')")
    value: str = Field(..., description="Value of the configuration parameter (stored as string, can be parsed to int, bool, etc.)")
    description: Optional[str] = Field(None, description="Description of the parameter's purpose")
    data_type_id: uuid.UUID = Field(..., description="ID of the MasterData entry indicating the data type of the value")
    is_active: Optional[bool] = Field(True, description="Indicates if the parameter is active and in use")

    model_config = ConfigDict(from_attributes=True)

class ConfigurationParameterCreate(ConfigurationParameterBase):
    pass

class ConfigurationParameterUpdate(ConfigurationParameterBase):
    name: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None
    data_type_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None

# --- Esquema de Lectura/Respuesta (con relaciones) ---
class ConfigurationParameter(ConfigurationParameterBase):
    id: uuid.UUID
    created_by_user_id: uuid.UUID # Quién creó/modificó el parámetro
    created_at: datetime
    updated_at: datetime

    # Relaciones cargadas para la respuesta
    data_type: Optional["MasterDataReduced"] = None
    created_by_user: Optional["UserReduced"] = None

    model_config = ConfigDict(from_attributes=True)
