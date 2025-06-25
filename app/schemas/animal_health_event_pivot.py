# app/schemas/animal_health_event_pivot.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime
import uuid

# Importa los schemas reducidos de las entidades relacionadas
from app.schemas.animal import AnimalReducedForAnimalGroup # Revisa cuál AnimalReduced es más apropiado aquí
from app.schemas.health_event import HealthEventReducedForPivot # Importa el schema reducido específico

# ForwardRefs para resolver dependencias circulares si las hubiera
# No necesitamos ForwardRef aquí si las referencias ya están importadas o son autodeclaradas.

# --- Esquemas Reducidos para AnimalHealthEventPivot ---
class AnimalHealthEventPivotReduced(BaseModel):
    id: uuid.UUID # El ID de la BaseModel
    animal_id: uuid.UUID
    health_event_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class AnimalHealthEventPivotReducedForHealthEvent(BaseModel): # Para ser usado cuando se consulta un HealthEvent
    id: uuid.UUID
    animal_id: uuid.UUID
    animal: Optional[AnimalReducedForAnimalGroup] = None # Para evitar recursión
    model_config = ConfigDict(from_attributes=True)

class AnimalHealthEventPivotReducedForAnimal(BaseModel): # Para ser usado cuando se consulta un Animal
    id: uuid.UUID
    health_event_id: uuid.UUID
    health_event: Optional[HealthEventReducedForPivot] = None # Para evitar recursión
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación/Actualización ---
class AnimalHealthEventPivotBase(BaseModel):
    animal_id: uuid.UUID = Field(..., description="ID of the animal involved in the health event")
    health_event_id: uuid.UUID = Field(..., description="ID of the health event")

    model_config = ConfigDict(from_attributes=True)

class AnimalHealthEventPivotCreate(AnimalHealthEventPivotBase):
    pass

# No hay un AnimalHealthEventPivotUpdate común ya que es una tabla pivot simple.
# La actualización se manejaría creando o eliminando entradas, o actualizando los eventos directamente.

# --- Esquema de Lectura/Respuesta (con relaciones) ---
class AnimalHealthEventPivot(AnimalHealthEventPivotBase):
    id: uuid.UUID # El ID de la BaseModel
    created_at: datetime
    updated_at: datetime

    # Relaciones directas (cargadas para la respuesta)
    animal: Optional[AnimalReducedForAnimalGroup] = None # Usar el schema reducido apropiado
    health_event: Optional[HealthEventReducedForPivot] = None # Usar el schema reducido específico

    model_config = ConfigDict(from_attributes=True)

