# app/models/lot.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, Numeric, DateTime, Boolean # ¡AÑADE Boolean aquí!
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from typing import List, Optional, ForwardRef

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Define ForwardRef para los modelos con los que Lot se relaciona
# y que pueden causar importación circular.
Farm = ForwardRef("Farm")
Animal = ForwardRef("Animal")
AnimalLocationHistory = ForwardRef("AnimalLocationHistory")

class Lot(BaseModel): # Hereda de BaseModel
    __tablename__ = "lots"
    # id, created_at, updated_at son heredados de BaseModel

    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    capacity = Column(Numeric(10, 2)) # Ej. número de animales o área
    is_active = Column(Boolean, default=True) # <-- Aquí se usaba Boolean sin importar

    # Relaciones
    farm: Mapped["Farm"] = relationship(Farm, back_populates="lots")
    animals: Mapped[List["Animal"]] = relationship(Animal, back_populates="current_lot")

    # Relación inversa con AnimalLocationHistory
    location_history_entries: Mapped[List["AnimalLocationHistory"]] = relationship(AnimalLocationHistory, back_populates="lot", cascade="all, delete-orphan")
