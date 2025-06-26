# app/models/role.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from app.db.base import BaseModel # Hereda de BaseModel

from typing import List, Optional, ForwardRef, TYPE_CHECKING # Importar TYPE_CHECKING
if TYPE_CHECKING:
    from .user import User
    from .permission import Permission
    from .user_role import UserRole # Para la tabla de asociación
    from .role_permission import RolePermission # Para la tabla de asociación

class Role(BaseModel):
    __tablename__ = "roles"

    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text)

    # Relación Many-to-Many con Permission a través de RolePermission
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary="role_permissions", # <-- ¡CORREGIDO a "role_permissions" si ese es el __tablename__!
        primaryjoin="Role.id == RolePermission.role_id", 
        secondaryjoin="Permission.id == RolePermission.permission_id", 
        back_populates="roles",
        overlaps="role_permissions_associations" # Añadido 'overlaps' para silenciar el warning
    )

    # Relación Many-to-Many con User a través de UserRole
    users_with_this_role: Mapped[List["User"]] = relationship(
        "User",
        secondary="user_roles", # Nombre de la tabla de asociación
        primaryjoin="Role.id == UserRole.role_id", 
        secondaryjoin="User.id == UserRole.user_id", 
        back_populates="roles_assigned_to_user",
        overlaps="user_roles_associations" # Añadido 'overlaps'
    )

    # Relaciones para las tablas de asociación (si las necesitas directamente)
    role_permissions_associations: Mapped[List["RolePermission"]] = relationship(
        "RolePermission", 
        back_populates="role", 
        cascade="all, delete-orphan",
        overlaps="permissions" # ¡Ajustado para el nombre de la relación Many-to-Many!
    )
    user_roles_associations: Mapped[List["UserRole"]] = relationship(
        "UserRole", 
        foreign_keys="[UserRole.role_id]", 
        back_populates="role", 
        cascade="all, delete-orphan",
        overlaps="users_with_this_role" # ¡Ajustado para el nombre de la relación Many-to-Many!
    )
