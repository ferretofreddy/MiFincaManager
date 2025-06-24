# app/models/animal_group.py
import uuid
from datetime import datetime
from sqlalchemy import Column, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.schema import PrimaryKeyConstraint
from typing import Optional, ForwardRef # ¡AÑADE ForwardRef aquí!

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel # Asumo que AnimalGroup hereda de BaseModel (o Base)

# No importes los modelos aquí si causan circularidad.
# from .animal import Animal # COMENTAR/ELIMINAR
# from .grupo import Grupo # COMENTAR/ELIMINAR

# Define ForwardRef para Animal y Grupo
User = ForwardRef("User")
Animal = ForwardRef("Animal") # <--- AÑADE ESTA LÍNEA
Grupo = ForwardRef("Grupo") # <--- AÑADE ESTA LÍNEA

class AnimalGroup(BaseModel): # O Base si es una tabla de pivote simple
    __tablename__ = "animal_group" # Asumo que es animal_group como nombre de tabla
    # id, created_at, updated_at son heredados de BaseModel.
    # Si esta es una tabla de pivote *sin* su propio ID, y con PK compuesta,
    # entonces no debería heredar de BaseModel, sino directamente de Base,
    # y definir sus primary_key=True en las columnas como en otros pivotes.
    # REVISIÓN: Tu repo tiene AnimalGroup heredando de BaseModel. Mantendré eso.

    animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), nullable=False)
    grupo_id = Column(UUID(as_uuid=True), ForeignKey("grupos.id"), nullable=False)
    assignment_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relaciones
    animal: Mapped["Animal"] = relationship(Animal, back_populates="groups_history") # <--- USA LA REFERENCIA STRING/ForwardRef
    grupo: Mapped["Grupo"] = relationship(Grupo, back_populates="animal_groups") # <--- USA LA REFERENCIA STRING/ForwardRef
    # Asumo que created_by_user ya lo tienes. Si no, necesitarías:
    # created_by_user: Mapped["User"] = relationship("User", back_populates="animal_groups_created")
