# app/models/role_permission.py
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from app.db.base import Base # Hereda directamente de Base

from typing import TYPE_CHECKING, Optional, List # Importar TYPE_CHECKING
if TYPE_CHECKING:
    from .role import Role
    from .permission import Permission

class RolePermission(Base): 
    __tablename__ = "role_permissions"
    
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True, index=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True, index=True)
    assigned_at = Column(DateTime, default=datetime.utcnow) 

    # Relaciones - Usando STRING LITERALS como ya lo hicimos
    role: Mapped["Role"] = relationship("Role", back_populates="role_permissions_associations") 
    permission: Mapped["Permission"] = relationship("Permission", back_populates="permission_roles_associations")

