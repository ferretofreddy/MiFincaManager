# app/models/user_farm_access.py
import uuid
from datetime import datetime
from sqlalchemy import Column, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.schema import PrimaryKeyConstraint
from typing import Optional, ForwardRef

# Importa BaseModel de nuestro módulo app/db/base.py
# Si esta es una tabla de pivote simple con PK compuesta, debería heredar de Base.
# Si tiene su propio ID de UUID, entonces BaseModel está bien.
# Dado tu patrón con otros pivotes, vamos a usar Base directamente con PK compuesta.
from app.db.base import Base # Usamos Base directamente para PrimaryKeyConstraint

# Define ForwardRef para User y Farm para evitar circularidad
User = ForwardRef("User")
Farm = ForwardRef("Farm")

class UserFarmAccess(Base): # Hereda de Base para PK compuesta
    __tablename__ = "user_farm_access"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True, nullable=False)
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"), primary_key=True, nullable=False)
    assigned_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False) # Quién asignó el acceso
    can_view = Column(Boolean, default=True, nullable=False)
    can_edit = Column(Boolean, default=False, nullable=False)
    can_manage_users = Column(Boolean, default=False, nullable=False) # Permiso específico para gestionar usuarios en esta finca
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text)

    # Definición de la clave primaria compuesta
    __table_args__ = (PrimaryKeyConstraint("user_id", "farm_id"),)

    # Relaciones ORM
    user: Mapped["User"] = relationship(User, foreign_keys=[user_id], back_populates="farm_accesses")
    farm: Mapped["Farm"] = relationship(Farm, back_populates="farm_accesses")
    assigned_by_user: Mapped["User"] = relationship(User, foreign_keys=[assigned_by_user_id], back_populates="accesses_assigned")
