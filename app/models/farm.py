# app/models/farm.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from typing import List, Optional, ForwardRef

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Define ForwardRef si es necesario (ej. para UserFarmAccess)
User = ForwardRef("User") 
Lot = ForwardRef("Lot")
Transaction = ForwardRef("Transaction")
Batch = ForwardRef("Batch")
Product = ForwardRef("Product")
UserFarmAccess = ForwardRef("UserFarmAccess") 
# Asegúrate de importar HealthEvent si lo usas, o ForwardRef si causa circularidad
HealthEvent = ForwardRef("HealthEvent") # <-- ¡AÑADIDO ForwardRef para HealthEvent!

class Farm(BaseModel): # Hereda de BaseModel
    __tablename__ = "farms"
    # id, created_at, updated_at son heredados de BaseModel

    name = Column(String, index=True, nullable=False)
    location = Column(String) # Ej. "Provincia, Cantón, Distrito"
    size_acres = Column(Numeric(10, 2))
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    # Relaciones directas e inversas - ¡Asegurar string literals!
    owner_user: Mapped["User"] = relationship("User", back_populates="farms_owned")
    lots: Mapped[List["Lot"]] = relationship("Lot", back_populates="farm", cascade="all, delete-orphan")
    farm_accesses: Mapped[List["UserFarmAccess"]] = relationship("UserFarmAccess", back_populates="farm", cascade="all, delete-orphan") # <-- ¡Asegurado string literal!
    outgoing_transactions: Mapped[List["Transaction"]] = relationship("Transaction", foreign_keys="[Transaction.source_farm_id]", back_populates="source_farm")
    incoming_transactions: Mapped[List["Transaction"]] = relationship("Transaction", foreign_keys="[Transaction.destination_farm_id]", back_populates="destination_farm")
    batches: Mapped[List["Batch"]] = relationship("Batch", back_populates="farm", cascade="all, delete-orphan") 
    products: Mapped[List["Product"]] = relationship("Product", back_populates="farm", cascade="all, delete-orphan") 

    # === ¡AÑADIDA ESTA RELACIÓN QUE FALTABA! ===
    health_events: Mapped[List["HealthEvent"]] = relationship("HealthEvent", back_populates="farm", cascade="all, delete-orphan")

