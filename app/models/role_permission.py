# app/models/role_permission.py
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

class RolePermission(BaseModel): # Hereda de BaseModel (aunque tiene PKs compuestas, mantiene created_at/updated_at)
    __tablename__ = "role_permissions"
    
    # Las columnas de clave primaria compuesta no deben ser generadas por BaseModel,
    # así que las definimos explícitamente y omitimos el 'id' auto-generado de BaseModel
    # Si BaseModel genera 'id' automáticamente, deberías eliminarlo de esta tabla
    # y solo usar role_id y permission_id como primary_key=True.
    # Dado que BaseModel ya maneja 'id', podemos mantenerlo si es deseable tener un ID único
    # además de la clave compuesta. Para una tabla de unión pura, es común que solo existan
    # las FKs como PKs. Si necesitas 'id' para otras operaciones, déjalo.
    # Por la definición anterior, parece que no usas un 'id' propio para RolePermission.
    # Por lo tanto, ajustamos para que role_id y permission_id sean las PKs.
    
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True, index=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True, index=True)
    assigned_at = Column(DateTime, default=datetime.utcnow) # Hora de asignación

    # Relaciones
    # Estas relaciones apuntan a los modelos Role y Permission
    # La back_populates debe coincidir con el nombre de la relación inversa en el otro modelo.
    # En Role, la relación con RolePermission se llamará 'role_permissions_associations'
    # En Permission, la relación con RolePermission se llamará 'permission_roles_associations'
    role = relationship("Role", back_populates="role_permissions_associations")
    permission = relationship("Permission", back_populates="permission_roles_associations")

