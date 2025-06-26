# app/models/transaction.py
import uuid
from datetime import datetime
from sqlalchemy import Column, ForeignKey, DateTime, Text, Numeric, String # Mantén String por si acaso
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from typing import Optional, ForwardRef, List # Añade List

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Definiciones de ForwardRef para los modelos con los que Transaction se relaciona
User = ForwardRef("User")
Farm = ForwardRef("Farm")
MasterData = ForwardRef("MasterData")

class Transaction(BaseModel): # Hereda de BaseModel
    __tablename__ = "transactions"
    # id, created_at, updated_at son heredados de BaseModel.

    transaction_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    transaction_type_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"), nullable=False) # Tipo de transacción (ej. compra, venta, traslado)
    
    # === ¡CAMBIOS AQUÍ! ===
    # Nueva columna para la FK al tipo de entidad en MasterData
    entity_type_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"), nullable=False) 
    # La columna 'entity_type' (String) se elimina o se usa solo para información auxiliar si es necesario.
    # Si entity_type es puramente un label y el ID es la FK, la cadena 'entity_type' ya no es necesaria como columna de DB.
    # Por ahora, la dejamos si la necesitas para algo más, pero la FK es entity_type_id.
    # Mejor: la quitamos si la FK es entity_type_id.
    # entity_type = Column(String, nullable=False) # <--- REMOVER ESTA LÍNEA

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
    
    # === ¡NUEVA RELACIÓN PARA entity_type_id! ===
    entity_type_md: Mapped["MasterData"] = relationship("MasterData", foreign_keys=[entity_type_id], back_populates="transactions_entity_type_md") # back_populates debe coincidir en MasterData

    unit: Mapped["MasterData"] = relationship("MasterData", foreign_keys=[unit_id], back_populates="transactions_unit")
    currency: Mapped["MasterData"] = relationship("MasterData", foreign_keys=[currency_id], back_populates="transactions_currency")
    recorded_by_user: Mapped["User"] = relationship("User", back_populates="transactions_recorded")
    source_farm: Mapped[Optional["Farm"]] = relationship("Farm", foreign_keys=[source_farm_id], back_populates="outgoing_transactions")
    destination_farm: Mapped[Optional["Farm"]] = relationship("Farm", foreign_keys=[destination_farm_id], back_populates="incoming_transactions")

    # NOTA: La lógica para cargar la entidad relacionada (Animal, Product, Batch) por entity_id
    # se manejará a nivel de CRUD y/o en los endpoints FastAPI de forma manual o con cargadores personalizados,
    # usando el `entity_type_md` para determinar el modelo.
