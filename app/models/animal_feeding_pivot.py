# app/models/animal_feeding_pivot.py
import uuid
from datetime import datetime
from sqlalchemy import Column, ForeignKey, DateTime, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.schema import PrimaryKeyConstraint # Para definir claves primarias compuestas
from typing import Optional

# Importa BaseModel de nuestro módulo app/db/base.py
# Aunque es una tabla de pivote, la definimos como un modelo para poder manejarla con BaseModel si es necesario,
# y para que Alembic la detecte. En este caso, no hereda de BaseModel directamente por las PK compuestas.
# Sin embargo, si tu BaseModel maneja 'id', 'created_at', 'updated_at' automáticamente, esta tabla de pivote
# que tiene PK compuestas y sus propios created_at/updated_at, podría ser una excepción.
# Para mantener la coherencia y que Alembic la detecte, la haremos heredar de BaseModel y asegurarnos
# de que no defina una 'id' propia si BaseModel ya la tiene, o ajustamos BaseModel.

from app.db.base import Base # Usamos Base directamente para PrimaryKeyConstraint

# Importa los modelos relacionados directamente
from .animal import Animal
from .feeding import Feeding

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
