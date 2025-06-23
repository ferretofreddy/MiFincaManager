# app/models/animal_group.py
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
from .grupo import Grupo
from .user import User

class AnimalGroup(BaseModel): # Hereda de BaseModel
    __tablename__ = "animal_groups"
    # id, created_at, updated_at son heredados de BaseModel.
    # Nota: Si el id auto-generado de BaseModel es suficiente, puedes eliminar primary_key=True de los campos de la PK compuesta.
    # Si quieres mantener la PK compuesta como antes, necesitarás una clave compuesta explícita
    # y manejar la asignación del ID en el CRUD, o confiar en que BaseModel lo maneje si no es una PK.
    # Para este ejemplo, asumiremos que BaseModel.id es la PK principal y que animal_id, group_id, assigned_at
    # son índices únicos/compuestos, o si son una PK compuesta se gestiona su generación.
    # Si quieres que animal_id, group_id, assigned_at sigan siendo la PK compuesta, tendríamos que reconfigurar.
    # Por la simplicidad y el uso de BaseModel, mantendremos BaseModel.id como PK.
    # Los campos anteriores se convierten en índices o parte de una restricción única.

    animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), nullable=False)
    group_id = Column(UUID(as_uuid=True), ForeignKey("grupos.id"), nullable=False)
    assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow) # Fecha de asignación al grupo
    removed_at = Column(DateTime, nullable=True) # Fecha de remoción del grupo
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relaciones
    animal: Mapped["Animal"] = relationship("Animal", back_populates="groups_history")
    grupo: Mapped["Grupo"] = relationship("Grupo", back_populates="animals_in_group")
    created_by_user: Mapped["User"] = relationship("User", back_populates="animal_groups_created")

    # Si necesitas una restricción de unicidad para la combinación de animal_id, group_id, assigned_at
    # __table_args__ = (UniqueConstraint("animal_id", "group_id", "assigned_at", name="uq_animal_group_association"),)
    # Sin embargo, si 'removed_at' puede ser nulo y quieres que un animal esté en un grupo a la vez:
    # Podrías necesitar lógica en el CRUD para asegurar que solo haya una entrada activa (removed_at is NULL)
    # por animal_id y group_id, o solo una por animal_id a la vez.
