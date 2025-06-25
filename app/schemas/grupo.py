# app/schemas/grupo.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime
import uuid

# Importa los schemas reducidos de las entidades relacionadas
from app.schemas.user import UserReduced
from app.schemas.master_data import MasterDataReduced

# --- Esquemas Reducidos para Grupo ---
class GrupoReduced(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    purpose_id: Optional[uuid.UUID] = None
    created_by_user_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class GrupoReducedForAnimalGroup(BaseModel): # Específico para AnimalGroup
    id: uuid.UUID
    name: str
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación/Actualización ---
class GrupoBase(BaseModel):
    name: str = Field(..., max_length=255, description="Name of the animal group")
    description: Optional[str] = None
    purpose_id: Optional[uuid.UUID] = Field(None, description="ID of the MasterData entry for the purpose of the group (e.g., 'fattening', 'breeding')")

class GrupoCreate(GrupoBase):
    pass # No necesita campos adicionales para la creación

class GrupoUpdate(GrupoBase):
    name: Optional[str] = None
    description: Optional[str] = None
    purpose_id: Optional[uuid.UUID] = None

# --- Esquema de Lectura/Respuesta (con relaciones) ---
class Grupo(GrupoBase):
    id: uuid.UUID
    created_by_user_id: uuid.UUID
    created_at: datetime # Heredado de BaseModel
    updated_at: datetime # Heredado de BaseModel

    # Relaciones directas (cargadas para la respuesta)
    purpose: Optional[MasterDataReduced] = None
    created_by_user: Optional[UserReduced] = None
    
    # Relación inversa con la tabla de asociación AnimalGroup
    animals_in_group: List[ForwardRef('AnimalGroupReducedForGrupo')] = [] # Usar ForwardRef para AnimalGroupReducedForGrupo

    model_config = ConfigDict(from_attributes=True)

