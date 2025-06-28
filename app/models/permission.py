# app/models/permission.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from app.db.base import BaseModel 

from typing import List, Optional, ForwardRef, TYPE_CHECKING 
if TYPE_CHECKING:
    from .module import Module
    from .role import Role
    from .role_permission import RolePermission 

class Permission(BaseModel):
    __tablename__ = "permissions"

    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text)
    module_id = Column(UUID(as_uuid=True), ForeignKey("modules.id"), nullable=False)

    # Relaciones
    module: Mapped["Module"] = relationship("Module", back_populates="permissions")

    # Relación Many-to-Many con Role a través de RolePermission
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary="role_permissions", 
        primaryjoin="Permission.id == RolePermission.permission_id", 
        secondaryjoin="Role.id == RolePermission.role_id", 
        back_populates="permissions",
        # Asegura que este overlaps es explícito
        overlaps="permission_roles_associations,RolePermission.permission" 
    )

    # Relación directa con la tabla de asociación (si es necesaria)
    permission_roles_associations: Mapped[List["RolePermission"]] = relationship(
        "RolePermission", 
        back_populates="permission", 
        cascade="all, delete-orphan",
        # Asegura que este overlaps es explícito
        overlaps="roles,RolePermission.permission" 
    )

