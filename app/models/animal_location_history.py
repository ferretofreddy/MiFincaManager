# app/models/animal_location_history.py
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
from .lot import Lot
from .user import User

class AnimalLocationHistory(BaseModel): # Hereda de BaseModel
    __tablename__ = "animal_location_history"
    # id, created_at, updated_at son heredados de BaseModel.
    # Al igual que con AnimalGroup, asumimos que BaseModel.id es la PK principal.
    # Si necesitas una PK compuesta de animal_id, lot_id, entry_date, me lo indicas.

    animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), nullable=False)
    lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"), nullable=False)
    entry_date = Column(DateTime, nullable=False, default=datetime.utcnow) # Fecha de entrada al lote
    departure_date = Column(DateTime, nullable=True) # Fecha de salida del lote
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relaciones
    animal: Mapped["Animal"] = relationship("Animal", back_populates="locations_history")
    lot: Mapped["Lot"] = relationship("Lot", back_populates="animals_history_in_lot")
    created_by_user: Mapped["User"] = relationship("User", back_populates="animal_location_history_created")

    # Si necesitas una restricción de unicidad para la combinación de animal_id, lot_id, entry_date
    # from sqlalchemy import UniqueConstraint
    # __table_args__ = (UniqueConstraint("animal_id", "lot_id", "entry_date", name="uq_animal_location_association"),)
