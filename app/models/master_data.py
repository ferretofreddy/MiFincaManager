# app/models/master_data.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from typing import List, Optional

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Importa los modelos relacionados directamente (solo para Mapped[List["..."]])
from .user import User
from .animal import Animal
from .health_event import HealthEvent
from .feeding import Feeding
from .transaction import Transaction
from .batch import Batch # ¡Nuevo! Importa el modelo Batch

class MasterData(BaseModel): # Hereda de BaseModel
    __tablename__ = "master_data"
    # id, created_at, updated_at son heredados de BaseModel

    name = Column(String, index=True, nullable=False)
    category = Column(String, index=True, nullable=False) # Ej: "species", "breed", "product", "unit_of_measure"
    value = Column(Text) # Puede ser una descripción, un valor numérico, etc.
    is_active = Column(Boolean, default=True)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relaciones inversas
    created_by_user: Mapped["User"] = relationship("User", back_populates="master_data_created")
    animals_species: Mapped[List["Animal"]] = relationship("Animal", foreign_keys="[Animal.species_id]", back_populates="species")
    animals_breed: Mapped[List["Animal"]] = relationship("Animal", foreign_keys="[Animal.breed_id]", back_populates="breed")
    health_events_product: Mapped[List["HealthEvent"]] = relationship("HealthEvent", foreign_keys="[HealthEvent.product_id]", back_populates="product")
    health_events_event_type: Mapped[List["HealthEvent"]] = relationship("HealthEvent", foreign_keys="[HealthEvent.event_type_id]", back_populates="event_type")
    feedings_feed_type: Mapped[List["Feeding"]] = relationship("Feeding", foreign_keys="[Feeding.feed_type_id]", back_populates="feed_type")
    feedings_unit: Mapped[List["Feeding"]] = relationship("Feeding", foreign_keys="[Feeding.unit_id]", back_populates="unit")
    transactions_transaction_type: Mapped[List["Transaction"]] = relationship("Transaction", foreign_keys="[Transaction.transaction_type_id]", back_populates="transaction_type")
    transactions_unit: Mapped[List["Transaction"]] = relationship("Transaction", foreign_keys="[Transaction.unit_id]", back_populates="unit")
    transactions_currency: Mapped[List["Transaction"]] = relationship("Transaction", foreign_keys="[Transaction.currency_id]", back_populates="currency")

    # ¡Nueva relación para Batch!
    batches_batch_type: Mapped[List["Batch"]] = relationship("Batch", foreign_keys="[Batch.batch_type_id]", back_populates="batch_type") # ¡Actualizado!

    # Añadir otras relaciones inversas cuando se migren los modelos
    # products_type: Mapped[List["Product"]] = relationship("Product", foreign_keys="[Product.product_type_id]", back_populates="product_type")
