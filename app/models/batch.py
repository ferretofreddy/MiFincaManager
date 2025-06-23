# app/models/batch.py
import uuid
from datetime import datetime
from sqlalchemy import Column, ForeignKey, DateTime, Text, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from typing import Optional, List

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Importa los modelos relacionados directamente
from .master_data import MasterData
from .user import User
from .farm import Farm
from .animal_batch_pivot import AnimalBatchPivot # Importamos la tabla de pivote

class Batch(BaseModel): # Hereda de BaseModel
    __tablename__ = "batches"
    # id, created_at, updated_at son heredados de BaseModel.

    name = Column(String, nullable=False)
    batch_type_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"), nullable=False) # Ej. "venta", "engorde", "tratamiento"
    description = Column(Text)
    start_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_date = Column(DateTime, nullable=True) # Opcional, para lotes con duración definida
    status = Column(String, nullable=False) # Ej. "activo", "completado", "cancelado"
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False) # Granja a la que pertenece el lote
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relaciones
    batch_type: Mapped["MasterData"] = relationship("MasterData", foreign_keys=[batch_type_id], back_populates="batches_batch_type")
    farm: Mapped["Farm"] = relationship("Farm", back_populates="batches")
    created_by_user: Mapped["User"] = relationship("User", back_populates="batches_created")
    
    # Relación inversa con AnimalBatchPivot (la tabla de pivote para animales asociados)
    animal_batches: Mapped[List["AnimalBatchPivot"]] = relationship("AnimalBatchPivot", back_populates="batch_event", cascade="all, delete-orphan")
    
    # Si Transaction tiene un FK directo a Batch, se añadiría aquí.
    # Por ahora, Transaction maneja un entity_id polimórfico, por lo que la relación
    # inversa se gestionaría a través de consultas en el CRUD de Transaction.
    # transactions: Mapped[List["Transaction"]] = relationship("Transaction", foreign_keys="[Transaction.entity_id]", back_populates="batch_entity", viewonly=True)
