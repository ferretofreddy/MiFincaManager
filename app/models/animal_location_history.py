# app/models/animal_location_history.py
import uuid
from datetime import datetime
from sqlalchemy import Column, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from typing import Optional, ForwardRef

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Define ForwardRef para los modelos con los que AnimalLocationHistory se relaciona
# y que pueden causar importación circular.
Lot = ForwardRef("Lot") # <--- AÑADE ESTA LÍNEA
Animal = ForwardRef("Animal")
User = ForwardRef("User")

class AnimalLocationHistory(BaseModel):
    __tablename__ = "animal_location_history"

    animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), nullable=False)
    lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"), nullable=False)
    change_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relaciones - USANDO REFERENCIAS DE STRING O FORWARDREF
    animal: Mapped["Animal"] = relationship("Animal", back_populates="locations_history")
    lot: Mapped["Lot"] = relationship("Lot", back_populates="location_history_entries") # <--- USA LA REFERENCIA STRING/ForwardRef
    created_by_user: Mapped["User"] = relationship("User", back_populates="animal_location_history_created")
