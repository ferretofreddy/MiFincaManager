# app/schemas/role_permission.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime
import uuid

# Define ForwardRef para esquemas si hay circularidad
RoleReduced = ForwardRef("RoleReduced")
PermissionReduced = ForwardRef("PermissionReduced")

# --- Esquemas para la Asociación Directa RolePermission ---
class RolePermissionBase(BaseModel):
    role_id: uuid.UUID = Field(..., description="The ID of the role in the association")
    permission_id: uuid.UUID = Field(..., description="The ID of the permission in the association")

class RolePermissionCreate(RolePermissionBase):
    pass # No necesita campos adicionales para la creación de una asociación

# No se suele usar un RolePermissionUpdate para tablas de unión simples,
# ya que la "actualización" sería más bien eliminar y recrear la asociación.
# class RolePermissionUpdate(RolePermissionBase):
#     pass

class RolePermission(RolePermissionBase):
    assigned_at: datetime # Campo adicional de la tabla de unión
    
    # Opcional: Incluir los objetos Role y Permission completos o reducidos
    # si se desea devolver la información completa de la asociación.
    role: Optional["RoleReduced"] = None # <--- USAR REFERENCIA STRING
    permission: Optional["PermissionReduced"] = None # <--- USAR REFERENCIA STRING

    model_config = ConfigDict(from_attributes=True)

