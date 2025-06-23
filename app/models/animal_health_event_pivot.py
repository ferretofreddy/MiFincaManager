# app/models/animal_health_event_pivot.py
import uuid
from datetime import datetime
from sqlalchemy import Column, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from typing import Optional

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Importa los modelos relacionados directamente
from .animal import Animal
from .health_event import HealthEvent

class AnimalHealthEventPivot(BaseModel): # Hereda de BaseModel
    __tablename__ = "animal_health_event_pivot"
    # id, created_at, updated_at son heredados de BaseModel.
    # Si necesitas una PK compuesta de animal_id, health_event_id, me lo indicas.

    animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), nullable=False)
    health_event_id = Column(UUID(as_uuid=True), ForeignKey("health_events.id"), nullable=False)

    # Relaciones
    animal: Mapped["Animal"] = relationship("Animal", back_populates="health_events_pivot")
    health_event: Mapped["HealthEvent"] = relationship("HealthEvent", back_populates="animals_affected")

    # Si necesitas una restricción de unicidad para la combinación de animal_id, health_event_id
    # from sqlalchemy import UniqueConstraint
    # __table_args__ = (UniqueConstraint("animal_id", "health_event_id", name="uq_animal_health_event_association"),)
