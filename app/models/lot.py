# app/models/lot.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from typing import List, Optional

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Importa los modelos relacionados directamente
from .farm import Farm
from .user import User
from .animal import Animal
from .animal_location_history import AnimalLocationHistory # ¡Nuevo! Importa el modelo AnimalLocationHistory

class Lot(BaseModel): # Hereda de BaseModel
    __tablename__ = "lots"
    # id, created_at, updated_at son heredados de BaseModel

    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    capacity = Column(Integer)
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relaciones
    farm: Mapped["Farm"] = relationship("Farm", back_populates="lots")
    created_by_user: Mapped["User"] = relationship("User", back_populates="lots_created")
    
    animals: Mapped[List["Animal"]] = relationship("Animal", back_populates="current_lot")
    # Relación inversa con la tabla de historial AnimalLocationHistory (¡Actualizada!)
    animals_history_in_lot: Mapped[List["AnimalLocationHistory"]] = relationship("AnimalLocationHistory", back_populates="lot", cascade="all, delete-orphan")
