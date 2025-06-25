# app/schemas/permission.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime
import uuid

# Importa RoleReduced de tu nuevo módulo de schemas de rol
RoleReduced = ForwardRef("RoleReduced")

# Importa ModuleReduced de tu nuevo módulo de schemas de módulo
ModuleReduced = ForwardRef("ModuleReduced")


# --- Esquemas Reducidos para Romper Ciclos de Recursión ---
# Puede que necesites este si Permission se anida en otros schemas
class PermissionReduced(BaseModel):
    id: uuid.UUID
    name: str
    module_id: Optional[uuid.UUID] = None
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación/Actualización ---
class PermissionBase(BaseModel):
    name: str = Field(..., description="Unique name of the permission (e.g., 'create_user', 'read_farm')")
    description: Optional[str] = None
    module_id: Optional[uuid.UUID] = Field(None, description="ID of the module this permission belongs to")

class PermissionCreate(PermissionBase):
    pass # No necesita campos adicionales para la creación

class PermissionUpdate(PermissionBase):
    name: Optional[str] = None
    description: Optional[str] = None
    module_id: Optional[uuid.UUID] = None

# --- Esquema de Lectura/Respuesta (con relaciones) ---
class Permission(PermissionBase):
    id: uuid.UUID
    created_at: datetime # Heredado de BaseModel
    updated_at: datetime # Heredado de BaseModel

    # Relaciones con otros Schemas
    module: Optional["ModuleReduced"] = None
    roles: List["RoleReduced"] = []

    model_config = ConfigDict(from_attributes=True)
