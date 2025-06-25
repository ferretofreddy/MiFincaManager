# app/schemas/token.py
from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timedelta

class Token(BaseModel):
    """
    Esquema Pydantic para el token de acceso JWT.
    """
    access_token: str
    token_type: str = "bearer" # Tipo de token, por defecto "bearer"

    model_config = ConfigDict(from_attributes=True)

class TokenPayload(BaseModel):
    """
    Esquema Pydantic para el payload (carga) del token JWT.
    El 'sub' (subject) generalmente es el ID del usuario.
    """
    sub: Optional[str] = None # 'sub' es el estándar para el sujeto del token (ej. user ID)
    exp: Optional[datetime] = None # Fecha de expiración (timestamp)
    # Puedes añadir más campos aquí si los necesitas en el payload,
    # como roles, permisos, etc.
    # roles: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)
