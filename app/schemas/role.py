# app/schemas/role.py
from typing import Optional, List, ForwardRef
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
import uuid

# Define ForwardRef para esquemas si hay circularidad
UserReduced = ForwardRef("UserReduced")
UserRole = ForwardRef("UserRole")
RolePermission = ForwardRef("RolePermission")

class RoleBase(BaseModel):
    name: str = Field(..., max_length=50, description="Nombre único del rol (ej. 'Administrador', 'Operador')")
    description: Optional[str] = Field(None, description="Descripción del rol")
    is_active: Optional[bool] = Field(True, description="Indica si el rol está activo")
    created_by_user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

class RoleCreate(RoleBase):
    pass

class RoleUpdate(RoleBase):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    created_by_user_id: Optional[uuid.UUID] = None # No debería ser actualizable por el usuario

class RoleReduced(BaseModel):
    id: uuid.UUID
    name: str
    model_config = ConfigDict(from_attributes=True)

class Role(RoleBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Relaciones de Pydantic
    users: List["UserReduced"] = Field(default_factory=list)
    role_permissions_associations: List["RolePermission"] = Field(default_factory=list)
    user_roles: List["UserRole"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

# Reconstruir los modelos para resolver ForwardRefs
RoleReduced.model_rebuild()
Role.model_rebuild()
