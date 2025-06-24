# app/db/base.py
import uuid
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID # Importa UUID para la columna id
from sqlalchemy.sql import func # Para las funciones de tiempo

# Declara una base de clases declarativa que se utilizará para todos los modelos de SQLAlchemy.
# Esta `Base` es fundamental para que Alembic pueda descubrir tus modelos
# y generar migraciones de base de datos.
Base = declarative_base()

class BaseModel(Base):
    """
    Base model that provides common fields like id, created_at, and updated_at.
    All application models will inherit from this BaseModel.
    """
    __abstract__ = True # Indica que esta clase no será una tabla en la base de datos, solo una base abstracta.

    # Usamos declared_attr para que las columnas se definan correctamente en las clases que heredan.
    @declared_attr
    def id(cls):
        # Asumiendo que quieres UUIDs para tus IDs primarios
        return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Nota: No hay __tablename__ aquí porque es una clase abstracta.
    # Cada modelo que herede de BaseModel deberá definir su propio __tablename__.
