# app/models/farm.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from typing import List, Optional, ForwardRef

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Importa los modelos relacionados directamente (solo para Mapped[List["..."]])
# from .user import User # Si la relación Farm-User es directa, la importamos. Si es circular, ForwardRef.
# Asumo que User se importa directamente en Farm sin circularidad con Farm

# Define ForwardRef si es necesario (ej. para UserFarmAccess)
User = ForwardRef("User") # Si Farm importa User en un ciclo
Lot = ForwardRef("Lot")
Transaction = ForwardRef("Transaction")
Batch = ForwardRef("Batch")
Product = ForwardRef("Product")
UserFarmAccess = ForwardRef("UserFarmAccess") # ¡NUEVO FORWARDREF!

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
    batches: Mapped[List["Batch"]] = relationship("Batch", back_populates="farm", cascade="all, delete-orphan") # ¡Actualizado!
    products: Mapped[List["Product"]] = relationship("Product", back_populates="farm", cascade="all, delete-orphan") # ¡NUEVO! Añade esta relación


    # Añadir otras relaciones inversas cuando se migren los modelos
    # products = relationship("Product", back_populates="farm")
