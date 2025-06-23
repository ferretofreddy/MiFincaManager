# app/models/user_role.py
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

class UserRole(BaseModel): # Hereda de BaseModel
    __tablename__ = "user_roles"
    
    # role_id y user_id forman la clave primaria compuesta
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True, index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True, index=True)
    assigned_at = Column(DateTime, default=datetime.utcnow) # Hora de asignación
    assigned_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True) # Quien asignó el rol

    # Relaciones
    # Estas relaciones apuntan a los modelos User y Role
    # Las back_populates deben coincidir con el nombre de la relación inversa en el otro modelo.
    # En User, la relación con UserRole se llamará 'user_roles_associations' (o similar)
    # En Role, la relación con UserRole se llamará 'user_roles_associations' (o similar)
    user = relationship("User", foreign_keys=[user_id], back_populates="user_roles_associations")
    role = relationship("Role", back_populates="user_roles_associations")
    
    # Para la relación de quién asignó el rol
    assigned_by_user = relationship("User", foreign_keys=[assigned_by_user_id], back_populates="assigned_roles")
