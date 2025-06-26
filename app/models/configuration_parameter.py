# app/models/configuration_parameter.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from typing import Optional, ForwardRef

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Define ForwardRef para los modelos con los que ConfigurationParameter se relaciona
# y que pueden causar importación circular.
MasterData = ForwardRef("MasterData")
User = ForwardRef("User")

class ConfigurationParameter(BaseModel):
    """
    Modelo de SQLAlchemy para la gestión de parámetros de configuración de la aplicación.
    Permite almacenar configuraciones dinámicas que no son hardcodeadas.
    """
    __tablename__ = "configuration_parameters"

    # id, created_at, updated_at son heredados de BaseModel.

    name = Column(String, unique=True, index=True, nullable=False, comment="Unique name of the configuration parameter")
    value = Column(Text, nullable=False, comment="Value of the parameter (stored as string, can be parsed based on data_type)")
    description = Column(Text, comment="Description of the parameter's purpose and usage")
    is_active = Column(Boolean, default=True, nullable=False, comment="Indicates if the parameter is active")

    # Foreign Key to MasterData for the data type of the parameter's value
    # (e.g., 'String', 'Integer', 'Boolean', 'JSON')
    data_type_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"), nullable=False, comment="ID of MasterData entry defining the value's data type")

    # Auditoría
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, comment="User who created this parameter")

    # Relaciones ORM - ¡Asegurarnos de que usen string literals!
    data_type: Mapped["MasterData"] = relationship("MasterData", back_populates="configuration_parameters_data_type") # <-- ¡back_populates ajustado!
    created_by_user: Mapped["User"] = relationship("User", back_populates="configuration_parameters_created")

    # Puedes añadir un @property para convertir el 'value' al tipo correcto
    # dependiendo de data_type_id, si es necesario.
