# app/models/weighing.py
import uuid
from datetime import datetime
from sqlalchemy import Column, ForeignKey, DateTime, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from typing import Optional

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Importa los modelos relacionados directamente
from .animal import Animal
from .user import User

class Weighing(BaseModel): # Hereda de BaseModel
    __tablename__ = "weighings"
    # id, created_at, updated_at son heredados de BaseModel.

    animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), nullable=False)
    weighing_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    weight_kg = Column(Numeric(10, 2), nullable=False) # Peso en kilogramos
    notes = Column(Text)
    recorded_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relaciones
    animal: Mapped["Animal"] = relationship("Animal", back_populates="weighings")
    recorded_by_user: Mapped["User"] = relationship("User", back_populates="weighings_recorded")
