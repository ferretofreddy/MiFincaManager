# app/models/master_data.py
import uuid
from datetime import datetime
# ¡AÑADE ForeignKey aquí!
from sqlalchemy import Column, String, Text, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from typing import List, Optional, Any, Dict, ForwardRef

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Define ForwardRef para los modelos con los que MasterData se relaciona
# y que pueden causar importación circular.
User = ForwardRef("User")
Animal = ForwardRef("Animal")
Grupo = ForwardRef("Grupo")
Feeding = ForwardRef("Feeding")
HealthEvent = ForwardRef("HealthEvent")
Transaction = ForwardRef("Transaction")
Batch = ForwardRef("Batch")
Product = ForwardRef("Product")
# ¡AÑADE ESTA LÍNEA!
ConfigurationParameter = ForwardRef("ConfigurationParameter")


class MasterData(BaseModel): # Hereda de BaseModel
    __tablename__ = "master_data"
    # id, created_at, updated_at son heredados de BaseModel

    category = Column(String, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    properties = Column(JSON, nullable=True) # Para datos JSONB
    is_active = Column(Boolean, default=True)

    # Auditoría
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relaciones ORM
    created_by_user: Mapped["User"] = relationship("User", back_populates="master_data_created")

    # Relaciones inversas (de MasterData a otros modelos)
    animals_species: Mapped[List["Animal"]] = relationship("Animal", foreign_keys="[Animal.species_id]", back_populates="species")
    animals_breed: Mapped[List["Animal"]] = relationship("Animal", foreign_keys="[Animal.breed_id]", back_populates="breed")
    grupos_purpose: Mapped[List["Grupo"]] = relationship("Grupo", back_populates="purpose")
    feedings_feed_type: Mapped[List["Feeding"]] = relationship("Feeding", foreign_keys="[Feeding.feed_type_id]", back_populates="feed_type")
    feedings_unit: Mapped[List["Feeding"]] = relationship("Feeding", foreign_keys="[Feeding.unit_id]", back_populates="unit")
    health_events_product: Mapped[List["HealthEvent"]] = relationship("HealthEvent", back_populates="product")
    health_events_unit: Mapped[List["HealthEvent"]] = relationship("HealthEvent", foreign_keys="[HealthEvent.unit_id]", back_populates="unit")
    transaction_record_type: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="transaction_type")
    transaction_unit: Mapped[List["Transaction"]] = relationship("Transaction", foreign_keys="[Transaction.unit_id]", back_populates="unit")
    transaction_currency: Mapped[List["Transaction"]] = relationship("Transaction", foreign_keys="[Transaction.currency_id]", back_populates="currency")
    batches_batch_type: Mapped[List["Batch"]] = relationship("Batch", back_populates="batch_type")
    products_as_type: Mapped[List["Product"]] = relationship("Product", foreign_keys="[Product.product_type_id]", back_populates="product_type")
    products_as_unit: Mapped[List["Product"]] = relationship("Product", foreign_keys="[Product.unit_id]", back_populates="unit")
    
    parameter_data_type: Mapped[List["ConfigurationParameter"]] = relationship(ConfigurationParameter, back_populates="data_type")

    # Asegúrate de que las constraints de unicidad o índices compuestos estén aquí
    # __table_args__ = (UniqueConstraint('category', 'name', name='unique_master_data_name_per_category'),)
