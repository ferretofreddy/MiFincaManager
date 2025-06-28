# app/models/user_role.py
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

class UserRole(BaseModel): # Hereda de BaseModel
    __tablename__ = "user_roles"
    
    # role_id y user_id forman la clave primaria compuesta
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True, index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True, index=True)
    assigned_at = Column(DateTime, default=datetime.utcnow) # Hora de asignación
    assigned_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True) # Quien asignó el rol

    # Relaciones - Usando STRING LITERALS como ya lo hicimos
    user: Mapped["User"] = relationship(
        "User", 
        foreign_keys=[user_id], 
        back_populates="user_roles_associations",
        # Asegura que este overlaps es explícito y cubre todos los caminos
        overlaps="roles_assigned_to_user,assigned_roles" 
    )
    role: Mapped["Role"] = relationship(
        "Role", 
        back_populates="user_roles_associations",
        # Asegura que este overlaps es explícito y cubre todos los caminos
        overlaps="users_with_this_role" 
    )
    
    # Para la relación de quién asignó el rol
    assigned_by_user: Mapped["User"] = relationship(
        "User", 
        foreign_keys=[assigned_by_user_id], 
        back_populates="assigned_roles",
        # Asegura que este overlaps es explícito
        overlaps="user_roles_associations,roles_assigned_to_user"
    )

