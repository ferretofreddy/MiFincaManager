# app/schemas/animal_group.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime
import uuid

# Importa los schemas reducidos de las entidades relacionadas
from app.schemas.animal import AnimalReduced, AnimalReducedForAnimalGroup
from app.schemas.grupo import GrupoReduced, GrupoReducedForAnimalGroup
from app.schemas.user import UserReduced

# --- Esquemas Reducidos para AnimalGroup ---
class AnimalGroupReduced(BaseModel):
    id: uuid.UUID # El ID de la BaseModel
    animal_id: uuid.UUID
    group_id: uuid.UUID
    assigned_at: datetime
    removed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class AnimalGroupReducedForAnimal(BaseModel): # Para ser usado cuando se consulta un Animal
    id: uuid.UUID
    group_id: uuid.UUID
    assigned_at: datetime
    removed_at: Optional[datetime] = None
    grupo: Optional[GrupoReducedForAnimalGroup] = None # Para evitar recursión
    model_config = ConfigDict(from_attributes=True)

class AnimalGroupReducedForGrupo(BaseModel): # Para ser usado cuando se consulta un Grupo
    id: uuid.UUID
    animal_id: uuid.UUID
    assigned_at: datetime
    removed_at: Optional[datetime] = None
    animal: Optional[AnimalReducedForAnimalGroup] = None # Para evitar recursión
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación/Actualización ---
class AnimalGroupBase(BaseModel):
    animal_id: uuid.UUID = Field(..., description="ID of the animal being assigned to a group")
    group_id: uuid.UUID = Field(..., description="ID of the group the animal is assigned to")
    assigned_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the animal was assigned to the group")
    removed_at: Optional[datetime] = Field(None, description="Timestamp when the animal was removed from the group (if applicable)")

    model_config = ConfigDict(from_attributes=True)

class AnimalGroupCreate(AnimalGroupBase):
    # Puedes añadir validaciones o lógica aquí si es necesario para la creación
    pass

class AnimalGroupUpdate(BaseModel):
    # Permite actualizar solo removed_at o cualquier otro campo que se pueda modificar
    removed_at: Optional[datetime] = Field(None, description="Timestamp when the animal was removed from the group")
    # Puedes añadir otros campos si son actualizables en una asociación existente
    # assigned_at: Optional[datetime] = None # Podría ser un error actualizar esto directamente
    model_config = ConfigDict(from_attributes=True)

# --- Esquema de Lectura/Respuesta (con relaciones) ---
class AnimalGroup(AnimalGroupBase):
    id: uuid.UUID # El ID de la BaseModel
    created_by_user_id: uuid.UUID
    created_at: datetime # Heredado de BaseModel
    updated_at: datetime # Heredado de BaseModel

    # Relaciones directas (cargadas para la respuesta)
    animal: Optional[AnimalReducedForAnimalGroup] = None # Usa el schema reducido
    grupo: Optional[GrupoReducedForAnimalGroup] = None   # Usa el schema reducido
    created_by_user: Optional[UserReduced] = None        # Usa el schema reducido

    model_config = ConfigDict(from_attributes=True)

