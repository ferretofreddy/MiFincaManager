# app/db/base.py
from sqlalchemy.ext.declarative import declarative_base

# Declara una base de clases declarativa que se utilizará para todos los modelos de SQLAlchemy.
# Esta `Base` es fundamental para que Alembic pueda descubrir tus modelos
# y generar migraciones de base de datos.
Base = declarative_base()