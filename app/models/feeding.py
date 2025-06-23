# app/models/feeding.py
import uuid
from datetime import datetime
from sqlalchemy import Column, ForeignKey, DateTime, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from typing import Optional, List

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Importa los modelos relacionados directamente
from .master_data import MasterData
from .user import User
from .animal_feeding_pivot import AnimalFeedingPivot # Importamos la tabla de pivote

class Feeding(BaseModel): # Hereda de BaseModel
    __tablename__ = "feedings"
    # id, created_at, updated_at son heredados de BaseModel.

    feeding_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    feed_type_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"), nullable=False) # Tipo de alimento (ej. concentrado, pasto)
    quantity = Column(Numeric(10, 2), nullable=False) # Cantidad total administrada
    unit_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"), nullable=False) # Unidad de medida (ej. kg, lb)
    notes = Column(Text)
    recorded_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relaciones
    feed_type: Mapped["MasterData"] = relationship("MasterData", foreign_keys=[feed_type_id], back_populates="feedings_feed_type")
    unit: Mapped["MasterData"] = relationship("MasterData", foreign_keys=[unit_id], back_populates="feedings_unit")
    recorded_by_user: Mapped["User"] = relationship("User", back_populates="feedings_recorded")
    
    # Relación inversa con AnimalFeedingPivot (la tabla de pivote para animales asociados)
    animal_feedings: Mapped[List["AnimalFeedingPivot"]] = relationship("AnimalFeedingPivot", back_populates="feeding_event", cascade="all, delete-orphan")
