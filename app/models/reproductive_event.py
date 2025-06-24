# app/models/reproductive_event.py
import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, ForeignKey, DateTime, Text, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from typing import Optional, List, ForwardRef

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Importa los modelos relacionados directamente
User = ForwardRef("User")
Animal = ForwardRef("Animal")
OffspringBorn = ForwardRef("OffspringBorn") 

class ReproductiveEvent(BaseModel): # Hereda de BaseModel
    __tablename__ = "reproductive_events"
    # id, created_at, updated_at son heredados de BaseModel.

    animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), nullable=False) # Animal hembra
    event_type = Column(String, nullable=False) # Se mapeará a ReproductiveEventTypeEnumPython
    event_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    description = Column(Text)
    sire_animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), nullable=True) # ID del semental, si aplica
    gestation_diagnosis_date = Column(DateTime, nullable=True)
    gestation_diagnosis_result = Column(String, nullable=True) # Se mapeará a GestationDiagnosisResultEnumPython
    expected_offspring_date = Column(Date, nullable=True)
    administered_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relaciones - USANDO REFERENCIAS DE STRING O FORWARDREF
    animal: Mapped["Animal"] = relationship(Animal, foreign_keys=[animal_id], back_populates="reproductive_events")
    sire_animal: Mapped[Optional["Animal"]] = relationship(Animal, foreign_keys=[sire_animal_id], back_populates="sire_reproductive_events")
    administered_by_user: Mapped["User"] = relationship(User, back_populates="reproductive_events_administered")
    
    # Relación inversa con OffspringBorn (si un evento reproductivo puede resultar en uno o más nacimientos)
    offspring_born_events: Mapped[List["OffspringBorn"]] = relationship(OffspringBorn, back_populates="reproductive_event", cascade="all, delete-orphan")
