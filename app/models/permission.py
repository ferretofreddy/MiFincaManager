# app/models/permission.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from app.db.base import BaseModel # Hereda de BaseModel

from typing import List, Optional, ForwardRef, TYPE_CHECKING # Importar TYPE_CHECKING
if TYPE_CHECKING:
    from .module import Module
    from .role import Role
    from .role_permission import RolePermission # Para la tabla de asociación

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
        secondary="role_permissions", # Nombre de la tabla de asociación
        primaryjoin="Permission.id == RolePermission.permission_id", # Cómo Permission se une a role_permissions
        secondaryjoin="Role.id == RolePermission.role_id", # Cómo Role se une a role_permissions
        back_populates="permissions",
        overlaps="permission_roles_associations" # Añadido 'overlaps' para silenciar el warning
    )

    # Relación directa con la tabla de asociación (si es necesaria)
    permission_roles_associations: Mapped[List["RolePermission"]] = relationship(
        "RolePermission", 
        back_populates="permission", 
        cascade="all, delete-orphan",
        overlaps="roles" # ¡Ajustado para el nombre de la relación Many-to-Many!
    )
