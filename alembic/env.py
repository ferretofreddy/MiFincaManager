# alembic/env.py
import asyncio # Importar asyncio
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.engine import Connection # Importar Connection para el tipo de hint
from sqlalchemy.ext.asyncio import AsyncEngine # Importar AsyncEngine
from sqlalchemy.schema import MetaData # Importar MetaData explícitamente si se usa
from sqlalchemy import text as sa_text # Importar text para ejecutar SQL plano si es necesario

from alembic import context

# this is the Alembic Config object, which provides
# access to values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import Base
# target_metadata = Base.metadata
# Importamos la base de datos y los modelos de tu aplicación
from database import Base # Asegúrate de que esta importación sea correcta
from models import * # Importar todos tus modelos para que Alembic los detecte
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an actual DBAPI connection.

    By skipping the connection the ALEMBIC_AUTO_GENERATE_REVISION
    flag (used by --autogenerate and revision --current) is
    honored, so the autogenerate process can still get
    a current metadata state.

    This is not a synchronous function; the context is set up
    and the migrations are run.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Función que ejecuta las migraciones. Se llama desde run_migrations_online.
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

# Cambiamos run_migrations_online para que sea una función asíncrona
async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            # No es necesario usar connect_args directamente aquí para el modo asyncpg
            # Alembic maneja los argumentos de conexión desde sqlalchemy.url
        )
    )

    async with connectable.connect() as connection:
        # Ejecutamos la función de migración de forma síncrona dentro del contexto asíncrono
        await connection.run_sync(do_run_migrations)


if context.is_offline_mode():
    run_migrations_offline()
else:
    # Si estamos en modo online, ejecutamos la función asíncrona dentro de un bucle de eventos
    asyncio.run(run_migrations_online())

