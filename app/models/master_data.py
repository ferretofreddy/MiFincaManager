# app/models/master_data.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from typing import List, ForwardRef, Optional

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Definiciones de ForwardRef para los modelos con los que MasterData se relaciona
User = ForwardRef("User")
Animal = ForwardRef("Animal")
HealthEvent = ForwardRef("HealthEvent")
Product = ForwardRef("Product")
Transaction = ForwardRef("Transaction")
Batch = ForwardRef("Batch")
Grupo = ForwardRef("Grupo")
ConfigurationParameter = ForwardRef("ConfigurationParameter") 

class MasterData(BaseModel):
    __tablename__ = "master_data"

    name = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_by_user: Mapped["User"] = relationship("User", back_populates="master_data_created")

    __table_args__ = (UniqueConstraint('category', 'name', name='unique_master_data_name_per_category'),)

    def __repr__(self):
        return f"<MasterData(name='{self.name}', category='{self.category}')>"

    # === RELACIONES INVERSAS (back_populates) ===
    animals_species: Mapped[List["Animal"]] = relationship("Animal", foreign_keys="[Animal.species_id]", back_populates="species")
    animals_breed: Mapped[List["Animal"]] = relationship("Animal", foreign_keys="[Animal.breed_id]", back_populates="breed")

    health_events_event_type: Mapped[List["HealthEvent"]] = relationship(
        "HealthEvent", 
        foreign_keys="[HealthEvent.event_type_id]", 
        back_populates="event_type" 
    )
    health_events_as_product: Mapped[List["HealthEvent"]] = relationship(
        "HealthEvent", 
        foreign_keys="[HealthEvent.product_id]", 
        back_populates="product" 
    )
    health_events_as_unit: Mapped[List["HealthEvent"]] = relationship(
        "HealthEvent", 
        foreign_keys="[HealthEvent.unit_id]", 
        back_populates="unit" 
    )

    feedings_feed_type: Mapped[List["Feeding"]] = relationship(
        "Feeding",
        foreign_keys="[Feeding.feed_type_id]",
        back_populates="feed_type"
    )
    feedings_unit: Mapped[List["Feeding"]] = relationship(
        "Feeding",
        foreign_keys="[Feeding.unit_id]",
        back_populates="unit"
    )

    # === ¡AÑADIDAS ESTAS DOS RELACIONES PARA Product.product_type y Product.unit! ===
    products_as_type: Mapped[List["Product"]] = relationship( # <-- ¡NUEVO NOMBRE que coincide!
        "Product",
        foreign_keys="[Product.product_type_id]", # Apunta a la FK correcta
        back_populates="product_type" # Coincide con la relación en Product
    )
    products_as_unit: Mapped[List["Product"]] = relationship( # <-- ¡NUEVO NOMBRE que coincide!
        "Product",
        foreign_keys="[Product.unit_id]", # Apunta a la FK correcta
        back_populates="unit" # Coincide con la relación en Product
    )

    transactions_transaction_type: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        foreign_keys="[Transaction.transaction_type_id]",
        back_populates="transaction_type"
    )
    transactions_entity_type_md: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        foreign_keys="[Transaction.entity_type_id]",
        back_populates="entity_type_md"
    )
    transactions_unit: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        foreign_keys="[Transaction.unit_id]",
        back_populates="unit"
    )
    transactions_currency: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        foreign_keys="[Transaction.currency_id]",
        back_populates="currency"
    )

    configuration_parameters_data_type: Mapped[List["ConfigurationParameter"]] = relationship(
        "ConfigurationParameter",
        foreign_keys="[ConfigurationParameter.data_type_id]",
        back_populates="data_type"
    )

    batches_batch_type: Mapped[List["Batch"]] = relationship(
        "Batch",
        foreign_keys="[Batch.batch_type_id]",
        back_populates="batch_type"
    )

    grupos_purpose: Mapped[List["Grupo"]] = relationship(
        "Grupo",
        foreign_keys="[Grupo.purpose_id]",
        back_populates="purpose"
    )
