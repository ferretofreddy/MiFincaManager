# app/models/permission.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Importa el modelo de asociación RolePermission y Module
from .role_permission import RolePermission
from .module import Module # Asegúrate de importar Module aquí si aún no lo está

class Permission(BaseModel): # Hereda de BaseModel
    __tablename__ = "permissions"
    # id, created_at, updated_at son heredados de BaseModel

    name = Column(String, unique=True, index=True, nullable=False) # Ej. "create_user", "read_farm"
    description = Column(String)
    module_id = Column(UUID(as_uuid=True), ForeignKey("modules.id"), nullable=True) # Módulo al que pertenece el permiso (e.g., 'users', 'farms')

    # Relaciones
    module = relationship("Module", back_populates="permissions")
    
    # Relación inversa a RolePermission
    permission_roles_associations = relationship(
        "RolePermission",
        back_populates="permission",
        cascade="all, delete-orphan" # Asegura que las asociaciones se eliminen si el permiso se elimina
    )

    # Relación de muchos-a-muchos a Role a través de RolePermission
    # Esto permite acceder directamente a los objetos Role desde un Permission
    roles = relationship(
        "Role",
        secondary="role_permissions", # Nombre de la tabla de unión
        back_populates="permissions" # Nombre de la relación inversa en el modelo Role
    )
