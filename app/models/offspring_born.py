# app/models/offspring_born.py
import uuid
from datetime import datetime, date
from sqlalchemy import Column, ForeignKey, DateTime, Text, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from typing import Optional, ForwardRef

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

Animal = ForwardRef("Animal")
User = ForwardRef("User")
ReproductiveEvent = ForwardRef("ReproductiveEvent")

class OffspringBorn(BaseModel): # Hereda de BaseModel
    __tablename__ = "offspring_born"
    # id, created_at, updated_at son heredados de BaseModel.

    reproductive_event_id = Column(UUID(as_uuid=True), ForeignKey("reproductive_events.id"), nullable=False)
    offspring_animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), nullable=True) # Si la cría se registra como un animal en el sistema
    date_of_birth = Column(DateTime, nullable=False, default=datetime.utcnow) # Fecha real de nacimiento de la cría
    notes = Column(Text)
    born_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False) # Usuario que registró el nacimiento

    # Relaciones - USANDO REFERENCIAS DE STRING O FORWARDREF
    reproductive_event: Mapped["ReproductiveEvent"] = relationship("ReproductiveEvent", back_populates="offspring_born_events")
    offspring_animal: Mapped[Optional["Animal"]] = relationship("Animal", foreign_keys=[offspring_animal_id], back_populates="offspring_born_events")
    born_by_user: Mapped["User"] = relationship("User", back_populates="offspring_born")
