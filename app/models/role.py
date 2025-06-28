# app/models/role.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean 
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from app.db.base import BaseModel 

from typing import List, Optional, ForwardRef, TYPE_CHECKING 
if TYPE_CHECKING:
    from .user import User
    from .permission import Permission
    from .user_role import UserRole 
    from .role_permission import RolePermission 

class Role(BaseModel):
    __tablename__ = "roles"

    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False) 
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_by_user: Mapped["User"] = relationship("User", back_populates="roles_created")


    # Relación Many-to-Many con Permission a través de RolePermission
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary="role_permissions", 
        primaryjoin="Role.id == RolePermission.role_id", 
        secondaryjoin="Permission.id == RolePermission.permission_id", 
        back_populates="roles",
        # Asegura que este overlaps es explícito
        overlaps="role_permissions_associations,RolePermission.role" 
    )

    # Relación Many-to-Many con User a través de UserRole
    users_with_this_role: Mapped[List["User"]] = relationship(
        "User",
        secondary="user_roles", 
        primaryjoin="Role.id == UserRole.role_id", 
        secondaryjoin="User.id == UserRole.user_id", 
        back_populates="roles_assigned_to_user",
        # Asegura que este overlaps es explícito
        overlaps="user_roles_associations,UserRole.role" 
    )

    # Relaciones para las tablas de asociación (si las necesitas directamente)
    role_permissions_associations: Mapped[List["RolePermission"]] = relationship(
        "RolePermission", 
        back_populates="role", 
        cascade="all, delete-orphan",
        # Asegura que este overlaps es explícito
        overlaps="permissions,RolePermission.role" 
    )
    user_roles_associations: Mapped[List["UserRole"]] = relationship(
        "UserRole", 
        foreign_keys="[UserRole.role_id]", 
        back_populates="role", 
        cascade="all, delete-orphan",
        # Asegura que este overlaps es explícito
        overlaps="users_with_this_role,UserRole.role" 
    )

    def __repr__(self):
        return f"<Role(name='{self.name}', id='{self.id}', is_active={self.is_active})>"

