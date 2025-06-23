# app/models/role.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Importa los modelos de asociación RolePermission y UserRole
from .role_permission import RolePermission
from .user_role import UserRole # Asegúrate de importar UserRole aquí

class Role(BaseModel): # Hereda de BaseModel
    __tablename__ = "roles"
    # id, created_at, updated_at son heredados de BaseModel

    name = Column(String, unique=True, index=True, nullable=False) # Ej. "admin", "viewer", "farm_manager"
    description = Column(String)

    # Relaciones
    # Relación inversa a RolePermission
    role_permissions_associations = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan"
    )
    # Relación de muchos-a-muchos a Permission a través de RolePermission
    permissions = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles"
    )

    # Relación inversa a UserRole (la asociación directa)
    user_roles_associations = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan" # Asegura que las asociaciones se eliminen si el rol se elimina
    )
    # Relación de muchos-a-muchos a User a través de UserRole
    # Esto permite acceder directamente a los objetos User desde un Role
    users = relationship(
        "User",
        secondary="user_roles", # Nombre de la tabla de unión
        back_populates="roles" # Nombre de la relación inversa en el modelo User
    )
