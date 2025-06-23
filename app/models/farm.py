# app/models/farm.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from typing import List, Optional

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Importa los modelos relacionados directamente (solo para Mapped[List["..."]])
from .user import User
from .lot import Lot
from .transaction import Transaction
from .batch import Batch # ¡Nuevo! Importa el modelo Batch

class Farm(BaseModel): # Hereda de BaseModel
    __tablename__ = "farms"
    # id, created_at, updated_at son heredados de BaseModel

    name = Column(String, index=True, nullable=False)
    location = Column(String) # Ej. "Provincia, Cantón, Distrito"
    size_acres = Column(Numeric(10, 2))
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    # Relaciones directas e inversas
    owner_user: Mapped["User"] = relationship("User", back_populates="farms_owned")
    lots: Mapped[List["Lot"]] = relationship("Lot", back_populates="farm", cascade="all, delete-orphan")
    farm_accesses = relationship("UserFarmAccess", back_populates="farm", cascade="all, delete-orphan")
    outgoing_transactions: Mapped[List["Transaction"]] = relationship("Transaction", foreign_keys="[Transaction.source_farm_id]", back_populates="source_farm")
    incoming_transactions: Mapped[List["Transaction"]] = relationship("Transaction", foreign_keys="[Transaction.destination_farm_id]", back_populates="destination_farm")
    
    # ¡Nueva relación para Batch!
    batches: Mapped[List["Batch"]] = relationship("Batch", back_populates="farm", cascade="all, delete-orphan") # ¡Actualizado!

    # Añadir otras relaciones inversas cuando se migren los modelos
    # products = relationship("Product", back_populates="farm")
