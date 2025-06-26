# app/models/animal.py
import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, ForeignKey, DateTime, Date, Text
from sqlalchemy.dialects.postgresql import UUID
# Importar 'remote' para relaciones auto-referenciadas
from sqlalchemy.orm import relationship, Mapped, remote # <-- ¡AÑADIDO remote!
from sqlalchemy.schema import UniqueConstraint
from typing import List, Optional, ForwardRef

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel 

# Definiciones de ForwardRef para los modelos con los que Animal se relaciona
User = ForwardRef("User") 
Animal = ForwardRef("Animal") # Para la auto-referencia
Lot = ForwardRef("Lot")
AnimalGroup = ForwardRef("AnimalGroup")
AnimalLocationHistory = ForwardRef("AnimalLocationHistory")
AnimalHealthEventPivot = ForwardRef("AnimalHealthEventPivot")
ReproductiveEvent = ForwardRef("ReproductiveEvent")
OffspringBorn = ForwardRef("OffspringBorn")
Weighing = ForwardRef("Weighing")
AnimalFeedingPivot = ForwardRef("AnimalFeedingPivot")
AnimalBatchPivot = ForwardRef("AnimalBatchPivot")

# Importa solo los modelos de MasterData que no causan circularidad
from .master_data import MasterData


class Animal(BaseModel):
    __tablename__ = "animals"

    tag_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    species_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"), nullable=True)
    breed_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"), nullable=True)
    sex = Column(String, nullable=False)
    date_of_birth = Column(Date)
    current_status = Column(String, nullable=False)
    origin = Column(String, nullable=False)
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

    # Relaciones auto-referenciadas - ¡CORREGIDAS CON primaryjoin y remote()!
    mother: Mapped[Optional["Animal"]] = relationship(
        "Animal",
        foreign_keys=[mother_animal_id],
        primaryjoin=lambda: Animal.mother_animal_id == remote(Animal.id), # <-- ¡CORREGIDO!
        back_populates="offspring_mother"
    )
    father: Mapped[Optional["Animal"]] = relationship(
        "Animal",
        foreign_keys=[father_animal_id],
        primaryjoin=lambda: Animal.father_animal_id == remote(Animal.id), # <-- ¡CORREGIDO!
        back_populates="offspring_father"
    )

    offspring_mother: Mapped[List["Animal"]] = relationship(
        "Animal",
        primaryjoin=lambda: Animal.id == remote(Animal.mother_animal_id), # <-- ¡CORREGIDO!
        back_populates="mother"
    )
    offspring_father: Mapped[List["Animal"]] = relationship(
        "Animal",
        primaryjoin=lambda: Animal.id == remote(Animal.father_animal_id), # <-- ¡CORREGIDO!
        back_populates="father"
    )

    # Relaciones con tablas de asociación y eventos
    groups_history: Mapped[List["AnimalGroup"]] = relationship("AnimalGroup", back_populates="animal", cascade="all, delete-orphan") 
    locations_history: Mapped[List["AnimalLocationHistory"]] = relationship("AnimalLocationHistory", back_populates="animal", cascade="all, delete-orphan") 
    health_events_pivot: Mapped[List["AnimalHealthEventPivot"]] = relationship("AnimalHealthEventPivot", back_populates="animal", cascade="all, delete-orphan") 
    reproductive_events: Mapped[List["ReproductiveEvent"]] = relationship("ReproductiveEvent", foreign_keys="[ReproductiveEvent.animal_id]", back_populates="animal") 
    sire_reproductive_events: Mapped[List["ReproductiveEvent"]] = relationship("ReproductiveEvent", foreign_keys="[ReproductiveEvent.sire_animal_id]", back_populates="sire_animal") 
    weighings: Mapped[List["Weighing"]] = relationship("Weighing", back_populates="animal", cascade="all, delete-orphan") 
    feedings_pivot: Mapped[List["AnimalFeedingPivot"]] = relationship("AnimalFeedingPivot", back_populates="animal", cascade="all, delete-orphan") 
    offspring_born_events: Mapped[List["OffspringBorn"]] = relationship("OffspringBorn", foreign_keys="[OffspringBorn.offspring_animal_id]", back_populates="offspring_animal") 
    batches_pivot: Mapped[List["AnimalBatchPivot"]] = relationship("AnimalBatchPivot", back_populates="animal", cascade="all, delete-orphan") 
