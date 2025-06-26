# app/models/animal_group.py
import uuid
from datetime import datetime
from sqlalchemy import Column, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.schema import PrimaryKeyConstraint
from typing import List, Optional, ForwardRef

from app.db.base import BaseModel # Asumo que AnimalGroup hereda de BaseModel (o Base)

# Define ForwardRef para Animal y Grupo (ya lo tenías)
User = ForwardRef("User")
Animal = ForwardRef("Animal")
Grupo = ForwardRef("Grupo")

class AnimalGroup(BaseModel): # O Base si es una tabla de pivote simple
    __tablename__ = "animal_group" 

    animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), nullable=False)
    grupo_id = Column(UUID(as_uuid=True), ForeignKey("grupos.id"), nullable=False)
    assignment_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relaciones - ¡CORREGIDO AQUÍ!
    animal: Mapped["Animal"] = relationship("Animal", back_populates="groups_history")
    grupo: Mapped["Grupo"] = relationship("Grupo", back_populates="animals_in_group")
    created_by_user: Mapped["User"] = relationship("User", back_populates="animal_groups_created")

    # Si tu tabla de pivote tiene una PK compuesta, asegúrate de definirla.
    # Si BaseModel ya añade 'id' como PK, entonces esta no es necesaria a menos que quieras una PK adicional.
    # __table_args__ = (PrimaryKeyConstraint('animal_id', 'grupo_id', name='pk_animal_group'),) # Ejemplo de PK compuesta


