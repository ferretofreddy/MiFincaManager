# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Clase que define la configuración de la aplicación.
# Hereda de BaseSettings para cargar variables de entorno automáticamente.
class Settings(BaseSettings):
    # Configuración de Pydantic para manejar el archivo .env
    model_config = SettingsConfigDict(
        env_file=".env",            # Especifica el archivo de entorno
        case_sensitive=True         # Las variables de entorno son sensibles a mayúsculas/minúsculas
    )

    # --- Configuración de la Base de Datos ---
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_PRE_PING: bool = True

    # --- Configuración de Seguridad (JWT) ---
    SECRET_KEY: str # No le asignes un valor aquí, se carga del .env
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # Este es un valor por defecto si no está en .env
    ALGORITHM: str = "HS256" # Este es un valor por defecto si no está en .env

    # --- Configuración General de la Aplicación ---
    DEBUG: bool = False # Este es un valor por defecto si no está en .env
    PROJECT_NAME: str = "MiFincaManager" # Este es un valor por defecto si no está en .env
    API_V1_STR: str = "/api/v1" # Este es un valor por defecto si no está en .env

    # --- Configuracion de super usuario (Admin) ---
    FIRST_SUPERUSER_EMAIL: str
    FIRST_SUPERUSER_PASSWORD: str

# Crea una instancia global de la configuración.
settings = Settings()
