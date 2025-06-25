# app/schemas/user_role.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime
import uuid

# Define ForwardRef para esquemas si hay circularidad
UserReduced = ForwardRef("UserReduced")
RoleReduced = ForwardRef("RoleReduced")

# --- Esquemas para la Asociación Directa UserRole ---
class UserRoleBase(BaseModel):
    user_id: uuid.UUID = Field(..., description="The ID of the user in the association")
    role_id: uuid.UUID = Field(..., description="The ID of the role in the association")
    assigned_by_user_id: Optional[uuid.UUID] = Field(None, description="The ID of the user who assigned this role")

class UserRoleCreate(UserRoleBase):
    pass # No necesita campos adicionales para la creación de una asociación

# No se suele usar un UserRoleUpdate para tablas de unión simples.
# class UserRoleUpdate(UserRoleBase):
#     pass

class UserRole(UserRoleBase):
    assigned_at: datetime # Campo adicional de la tabla de unión
    
    # Opcional: Incluir los objetos User y Role completos o reducidos
    user: Optional["UserReduced"] = None # <--- USAR REFERENCIA STRING
    role: Optional["RoleReduced"] = None # <--- USAR REFERENCIA STRING
    assigned_by_user: Optional["UserReduced"] = None # Quien asignó el rol # <--- USAR REFERENCIA STRING

    model_config = ConfigDict(from_attributes=True)

