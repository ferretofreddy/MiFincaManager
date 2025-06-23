# app/models/transaction.py
import uuid
from datetime import datetime
from sqlalchemy import Column, ForeignKey, DateTime, Text, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from typing import Optional

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Importa los modelos relacionados directamente
from .master_data import MasterData
from .user import User
from .farm import Farm
# Si Transaction se relaciona con Animal, Product, Batch directamente,
# estos NO se importan aquí para la relación polimórfica manual.
# from .animal import Animal
# from .product import Product
# from .batch import Batch

class Transaction(BaseModel): # Hereda de BaseModel
    __tablename__ = "transactions"
    # id, created_at, updated_at son heredados de BaseModel.

    transaction_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    transaction_type_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"), nullable=False) # Tipo de transacción (ej. compra, venta, traslado)
    entity_type = Column(String, nullable=False) # Tipo de entidad (ej. 'Animal', 'Product', 'Batch')
    entity_id = Column(UUID(as_uuid=True), nullable=False) # ID de la entidad involucrada (animal, producto, etc.)
    quantity = Column(Numeric(10, 2), nullable=True) # Cantidad si es aplicable (ej. kg de carne, número de animales)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"), nullable=True) # Unidad de medida (ej. kg, unidad)
    price_per_unit = Column(Numeric(10, 2), nullable=True)
    total_amount = Column(Numeric(10, 2), nullable=True)
    currency_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"), nullable=True) # Tipo de moneda (ej. USD, CRC)
    notes = Column(Text)
    recorded_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    source_farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"), nullable=True)
    destination_farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"), nullable=True)

    # Relaciones directas
    transaction_type: Mapped["MasterData"] = relationship("MasterData", foreign_keys=[transaction_type_id], back_populates="transactions_transaction_type")
    unit: Mapped["MasterData"] = relationship("MasterData", foreign_keys=[unit_id], back_populates="transactions_unit")
    currency: Mapped["MasterData"] = relationship("MasterData", foreign_keys=[currency_id], back_populates="transactions_currency")
    recorded_by_user: Mapped["User"] = relationship("User", back_populates="transactions_recorded")
    source_farm: Mapped[Optional["Farm"]] = relationship("Farm", foreign_keys=[source_farm_id], back_populates="outgoing_transactions")
    destination_farm: Mapped[Optional["Farm"]] = relationship("Farm", foreign_keys=[destination_farm_id], back_populates="incoming_transactions")

    # NOTA: No hay una relación 'relationship' directa para entity_id/entity_type aquí.
    # La lógica para cargar la entidad relacionada (Animal, Product, Batch) se manejará
    # a nivel de CRUD y/o en los endpoints FastAPI de forma manual o con cargadores personalizados.
