# app/models/module.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

class Module(BaseModel): # Hereda de BaseModel
    __tablename__ = "modules"
    # id, created_at, updated_at son heredados de BaseModel

    name = Column(String, unique=True, index=True, nullable=False) # Ej. "users", "farms", "animals"
    description = Column(String)

    # Relaciones
    # Nota: Permission aún debe ser importado o definido.
    # Por ahora, la dejamos como cadena y la resolveremos cuando migremos ese modelo.
    permissions = relationship("Permission", back_populates="module")
