# app/models/animal_feeding_pivot.py
import uuid
from datetime import datetime
from sqlalchemy import Column, ForeignKey, DateTime, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.schema import PrimaryKeyConstraint
from typing import Optional, ForwardRef

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import Base

# Importa los modelos relacionados directamente
Animal = ForwardRef("Animal")
Feeding = ForwardRef("Feeding")

class AnimalFeedingPivot(Base): # Hereda de Base directamente por la PK compuesta
    __tablename__ = "animal_feeding_pivot"
    
    animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), primary_key=True)
    feeding_event_id = Column(UUID(as_uuid=True), ForeignKey("feedings.id"), primary_key=True)
    
    quantity_fed = Column(Numeric(10, 2), nullable=True) # Cantidad específica para este animal en este evento (si difiere del total)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Definición de la clave primaria compuesta
    __table_args__ = (PrimaryKeyConstraint("animal_id", "feeding_event_id"),)

    # Relaciones
    animal: Mapped["Animal"] = relationship("Animal", back_populates="feedings_pivot")
    feeding_event: Mapped["Feeding"] = relationship("Feeding", back_populates="animal_feedings")
