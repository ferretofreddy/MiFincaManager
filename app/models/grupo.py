# app/models/grupo.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from typing import List, Optional

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Importa los modelos relacionados directamente
from .user import User
from .master_data import MasterData
from .animal_group import AnimalGroup # ¡Nuevo! Importa el modelo AnimalGroup

class Grupo(BaseModel): # Hereda de BaseModel
    __tablename__ = "grupos"
    # id, created_at, updated_at son heredados de BaseModel

    name = Column(String, unique=True, index=True, nullable=False) # Puede ser único globalmente o por user_id, ajustar si es necesario
    description = Column(String)
    purpose_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"), nullable=True) # Tipo de grupo (ej. "engorde", "reproduccion")
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relaciones
    purpose: Mapped[Optional["MasterData"]] = relationship("MasterData", back_populates="grupos_purpose")
    created_by_user: Mapped["User"] = relationship("User", back_populates="grupos_created")
    
    # Relación inversa con la tabla de asociación AnimalGroup (¡Actualizada!)
    animals_in_group: Mapped[List["AnimalGroup"]] = relationship("AnimalGroup", back_populates="grupo", cascade="all, delete-orphan")
