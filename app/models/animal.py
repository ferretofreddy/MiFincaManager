# app/models/animal.py
import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, ForeignKey, DateTime, Date, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.schema import UniqueConstraint
from typing import List, Optional

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Importa los modelos relacionados directamente
from .user import User
from .master_data import MasterData
from .lot import Lot
from .animal_group import AnimalGroup
from .animal_location_history import AnimalLocationHistory
from .animal_health_event_pivot import AnimalHealthEventPivot
from .reproductive_event import ReproductiveEvent
from .offspring_born import OffspringBorn
from .weighing import Weighing
from .animal_feeding_pivot import AnimalFeedingPivot
from .animal_batch_pivot import AnimalBatchPivot # ¡Nuevo! Importa el modelo AnimalBatchPivot

class Animal(BaseModel): # Hereda de BaseModel
    __tablename__ = "animals"
    # id, created_at, updated_at son heredados de BaseModel

    tag_id = Column(String, unique=True, index=True, nullable=False) # ID único del animal (ej. chip, caravana)
    name = Column(String)
    species_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"), nullable=True)
    breed_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"), nullable=True)
    sex = Column(String, nullable=False) # Se mapeará a SexEnumPython
    date_of_birth = Column(Date)
    current_status = Column(String, nullable=False) # Se mapeará a AnimalStatusEnumPython
    origin = Column(String, nullable=False) # Se mapeará a AnimalOriginEnumPython
    mother_animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), nullable=True)
    father_animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), nullable=True)
    description = Column(Text)
    photo_url = Column(String)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    current_lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"), nullable=True)

    # Relaciones Directas e Inversas
    owner_user: Mapped["User"] = relationship("User", back_populates="animals_owned")
    species: Mapped["MasterData"] = relationship("MasterData", foreign_keys=[species_id], back_populates="animals_species")
    breed: Mapped["MasterData"] = relationship("MasterData", foreign_keys=[breed_id], back_populates="animals_breed")
    current_lot: Mapped["Lot"] = relationship("Lot", back_populates="animals")

    # Relaciones auto-referenciadas
    mother: Mapped[Optional["Animal"]] = relationship("Animal", remote_side=[id], foreign_keys=[mother_animal_id], back_populates="offspring_mother")
    father: Mapped[Optional["Animal"]] = relationship("Animal", remote_side=[id], foreign_keys=[father_animal_id], back_populates="offspring_father")

    offspring_mother: Mapped[List["Animal"]] = relationship("Animal", back_populates="mother", remote_side=[mother_animal_id])
    offspring_father: Mapped[List["Animal"]] = relationship("Animal", back_populates="father", remote_side=[father_animal_id])

    # Relaciones con tablas de asociación y eventos
    groups_history: Mapped[List["AnimalGroup"]] = relationship("AnimalGroup", back_populates="animal", cascade="all, delete-orphan")
    locations_history: Mapped[List["AnimalLocationHistory"]] = relationship("AnimalLocationHistory", back_populates="animal", cascade="all, delete-orphan")
    health_events_pivot: Mapped[List["AnimalHealthEventPivot"]] = relationship("AnimalHealthEventPivot", back_populates="animal", cascade="all, delete-orphan")
    reproductive_events: Mapped[List["ReproductiveEvent"]] = relationship("ReproductiveEvent", foreign_keys="[ReproductiveEvent.animal_id]", back_populates="animal")
    sire_reproductive_events: Mapped[List["ReproductiveEvent"]] = relationship("ReproductiveEvent", foreign_keys="[ReproductiveEvent.sire_animal_id]", back_populates="sire_animal")
    weighings: Mapped[List["Weighing"]] = relationship("Weighing", back_populates="animal", cascade="all, delete-orphan")
    feedings_pivot: Mapped[List["AnimalFeedingPivot"]] = relationship("AnimalFeedingPivot", back_populates="animal", cascade="all, delete-orphan")
    offspring_born_events: Mapped[List["OffspringBorn"]] = relationship("OffspringBorn", foreign_keys="[OffspringBorn.offspring_animal_id]", back_populates="offspring_animal")

    # ¡Nueva relación para Batch!
    batches_pivot: Mapped[List["AnimalBatchPivot"]] = relationship("AnimalBatchPivot", back_populates="animal", cascade="all, delete-orphan") # ¡Actualizado!

    # Si Transaction tuviera un FK directo a Animal
    # transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="animal")

    # Si necesitas una restricción única compuesta (ej. tag_id y owner_user_id)
    # __table_args__ = (UniqueConstraint("tag_id", "owner_user_id", name="uq_animal_tag_owner"),)
