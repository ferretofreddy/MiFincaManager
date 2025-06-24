# app/models/health_event.py
import uuid
from datetime import datetime
from sqlalchemy import Column, ForeignKey, DateTime, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from typing import Optional, List, ForwardRef # ¡AÑADE ForwardRef aquí!

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# No importes los modelos aquí si causan circularidad.
# from .master_data import MasterData # <--- ¡COMENTA O ELIMINA ESTA LÍNEA AQUÍ!
# from .user import User # Si User causa circularidad con HealthEvent
# from .animal_health_event_pivot import AnimalHealthEventPivot # Si AnimalHealthEventPivot causa circularidad
# from .farm import Farm # Si Farm causa circularidad

# Define ForwardRef para los modelos con los que HealthEvent se relaciona
# y que pueden causar importación circular.
MasterData = ForwardRef("MasterData") # <--- AÑADE ESTA LÍNEA
User = ForwardRef("User")
Animal = ForwardRef("Animal")
Farm = ForwardRef("Farm")
AnimalHealthEventPivot = ForwardRef("AnimalHealthEventPivot")


class HealthEvent(BaseModel):
    __tablename__ = "health_events"

    event_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    event_type_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"), nullable=False) # Ej. "Vacunación", "Desparasitación", "Tratamiento"
    product_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"), nullable=True) # Producto usado (ej. nombre de la vacuna, desparasitante)
    quantity = Column(Numeric(10, 2), nullable=True)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"), nullable=True) # Unidad del producto
    notes = Column(Text)
    administered_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False) # Finca donde ocurrió el evento

    # Relaciones - USANDO REFERENCIAS DE STRING O FORWARDREF
    event_type: Mapped["MasterData"] = relationship(MasterData, foreign_keys=[event_type_id], back_populates="health_events_event_type")
    product: Mapped[Optional["MasterData"]] = relationship(MasterData, foreign_keys=[product_id], back_populates="health_events_as_product") # Ajusta el back_populates si ya existe
    unit: Mapped[Optional["MasterData"]] = relationship(MasterData, foreign_keys=[unit_id], back_populates="health_events_as_unit") # Ajusta el back_populates si ya existe
    administered_by_user: Mapped["User"] = relationship(User, back_populates="health_events_administered")
    farm: Mapped["Farm"] = relationship(Farm, back_populates="health_events")
    
    # Relación inversa con AnimalHealthEventPivot
    animal_health_events_pivot: Mapped[List["AnimalHealthEventPivot"]] = relationship(AnimalHealthEventPivot, back_populates="health_event", cascade="all, delete-orphan")
