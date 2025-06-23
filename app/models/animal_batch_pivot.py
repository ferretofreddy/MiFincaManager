# app/models/animal_batch_pivot.py
import uuid
from datetime import datetime
from sqlalchemy import Column, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.schema import PrimaryKeyConstraint # Para definir claves primarias compuestas
from typing import Optional

# Importa Base de nuestro módulo app/db/base.py
from app.db.base import Base # Usamos Base directamente para PrimaryKeyConstraint

# Importa los modelos relacionados directamente
from .animal import Animal
from .batch import Batch

class AnimalBatchPivot(Base): # Hereda de Base directamente por la PK compuesta
    __tablename__ = "animal_batch_pivot"
    
    animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), primary_key=True)
    batch_event_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"), primary_key=True)
    
    assigned_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Definición de la clave primaria compuesta
    __table_args__ = (PrimaryKeyConstraint("animal_id", "batch_event_id"),)

    # Relaciones
    animal: Mapped["Animal"] = relationship("Animal", back_populates="batches_pivot")
    batch_event: Mapped["Batch"] = relationship("Batch", back_populates="animal_batches")
