# app/schemas/role.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime
import uuid

# --- Esquemas Reducidos para Romper Ciclos de Recursión ---
# Puede que necesites este si Role se anida en otros schemas
class RoleReduced(BaseModel):
    id: uuid.UUID
    name: str
    model_config = ConfigDict(from_attributes=True)

# --- Esquemas Base para Creación/Actualización ---
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass # No necesita campos adicionales para la creación

class RoleUpdate(RoleBase):
    name: Optional[str] = None
    description: Optional[str] = None

# --- Esquema de Lectura/Respuesta (con relaciones) ---
class Role(RoleBase):
    id: uuid.UUID
    created_at: datetime # Heredado de BaseModel
    updated_at: datetime # Heredado de BaseModel

    # Relaciones con otros Schemas
    # Usaremos ForwardRef para Permission y UserReduced, que se resolverán más tarde
    permissions: List[ForwardRef('PermissionReduced')] = [] # Asume que PermissionReduced existirá
    users: List[ForwardRef('UserReduced')] = [] # Para la relación inversa con User

    model_config = ConfigDict(from_attributes=True)

# Reconstruir los modelos para resolver ForwardRefs (si los hay)
RoleReduced.model_rebuild()
Role.model_rebuild()
