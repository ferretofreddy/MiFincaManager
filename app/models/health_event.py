# app/models/health_event.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from typing import Optional, List

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Importa los modelos relacionados directamente
from .user import User
from .master_data import MasterData
# No importamos Animal directamente aquí, ya que la relación es a través de AnimalHealthEventPivot

class HealthEvent(BaseModel): # Hereda de BaseModel
    __tablename__ = "health_events"
    # id, created_at, updated_at son heredados de BaseModel.

    event_type = Column(String, nullable=False) # Se mapeará a HealthEventTypeEnumPython
    event_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    description = Column(Text)
    product_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"), nullable=True) # Medicamento o producto usado
    quantity = Column(Numeric(10, 2), nullable=True)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"), nullable=True) # Unidad de medida del producto (ml, mg, etc.)
    administered_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relaciones
    product: Mapped[Optional["MasterData"]] = relationship("MasterData", foreign_keys=[product_id], back_populates="health_events_as_product")
    unit: Mapped[Optional["MasterData"]] = relationship("MasterData", foreign_keys=[unit_id], back_populates="health_events_as_unit")
    administered_by_user: Mapped["User"] = relationship("User", back_populates="health_events_administered")

    # Relaciones con la tabla pivot AnimalHealthEventPivot
    # Nota: Mapped[] es para el tipo de hint de la relación, no para el tipo de objeto en la lista
    animals_affected: Mapped[List["AnimalHealthEventPivot"]] = relationship(
        "AnimalHealthEventPivot", back_populates="health_event", cascade="all, delete-orphan"
    )
