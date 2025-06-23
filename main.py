# main.py
from fastapi import FastAPI
from routers import (
    users, 
    farms, 
    animals, 
    master_data, 
    lots, 
    grupos,
    animal_groups,
    health_events, 
    reproductive_events, 
    weighings, 
    feedings, 
    transactions,
    roles, # NUEVO: Importar el router de roles
    permissions, # NUEVO: Importar el router de permisos
    configuration_parameters, # NUEVO: Importar el router de parámetros de configuración
    animal_locations_history # NUEVO: Importar el router de historial de ubicaciones
)
from database import Base, engine, AsyncSessionLocal # Asegúrate de que AsyncSessionLocal esté aquí
from alembic.config import Config
from alembic import command
import os

app = FastAPI(
    title="MiFincaManager API",
    description="API para la gestión integral de fincas ganaderas.",
    version="1.0.0",
)

# Función para ejecutar migraciones de Alembic
async def run_migrations():
    """Ejecuta las migraciones de la base de datos al inicio de la aplicación."""
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("scriptlocation", "alembic")
    alembic_cfg.set_main_option("sqlalchemy.url", str(engine.url))
    
    # Asegúrate de que la carpeta de versiones exista
    versions_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'alembic', 'versions')
    os.makedirs(versions_path, exist_ok=True)

    try:
        # Esto se conecta directamente a la DB, no usa la sesión de FastAPI
        print("Running Alembic migrations...")
        command.upgrade(alembic_cfg, "head")
        print("Alembic migrations completed.")
    except Exception as e:
        print(f"Error running Alembic migrations: {e}")
        # Considera si quieres que la aplicación falle al iniciar si las migraciones fallan
        raise

@app.on_event("startup")
async def startup_event():
    """Evento que se ejecuta al iniciar la aplicación."""
    # Descomenta la línea de abajo si quieres ejecutar migraciones automáticas al iniciar.
    # Es útil en desarrollo, pero en producción podrías querer un control más manual.
    # await run_migrations()
    pass


# Incluir los routers en la aplicación FastAPI
app.include_router(users.router)
app.include_router(farms.router)
app.include_router(animals.router)
app.include_router(master_data.router)
app.include_router(lots.router)
app.include_router(grupos.router)
app.include_router(animal_groups.router)
app.include_router(health_events.router)
app.include_router(reproductive_events.router)
app.include_router(weighings.router)
app.include_router(feedings.router)
app.include_router(transactions.router)
app.include_router(roles.router)
app.include_router(permissions.router)
app.include_router(configuration_parameters.router)
app.include_router(animal_locations_history.router)

@app.get("/")
async def read_root():
    return {"message": "Welcome to MiFincaManager API"}

