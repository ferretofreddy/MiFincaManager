# app/schemas/module.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime
import uuid

# Importa PermissionReduced de tu nuevo módulo de schemas de permiso
from app.schemas.permission import PermissionReduced

# --- Esquemas Reducidos para Romper Ciclos de Recursión ---
# Puede que necesites este si Module se anida en otros schemas
class ModuleReduced(BaseModel):
    id: uuid.UUID
    name: str
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación/Actualización ---
class ModuleBase(BaseModel):
    name: str = Field(..., description="Unique name of the module (e.g., 'users', 'farms')")
    description: Optional[str] = None

class ModuleCreate(ModuleBase):
    pass # No necesita campos adicionales para la creación

class ModuleUpdate(ModuleBase):
    name: Optional[str] = None
    description: Optional[str] = None

# --- Esquema de Lectura/Respuesta (con relaciones) ---
class Module(ModuleBase):
    id: uuid.UUID
    created_at: datetime # Heredado de BaseModel
    updated_at: datetime # Heredado de BaseModel

    # Relaciones con otros Schemas
    permissions: List[PermissionReduced] = [] # Para la relación inversa con Permission

    model_config = ConfigDict(from_attributes=True)

# Reconstruir los modelos para resolver ForwardRefs (si los hay)
ModuleReduced.model_rebuild()
Module.model_rebuild()
