# auth.py
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from dotenv import load_dotenv
import os

# Cargar variables de entorno (asegúrate de que este archivo también cargue .env)
load_dotenv()

# Configuración de Passlib para el hasheo de contraseñas
# Usamos bcrypt, un algoritmo de hasheo recomendado para contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuración de JWT
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)) # Valor por defecto si no está en .env

if not SECRET_KEY or not ALGORITHM:
    raise ValueError("SECRET_KEY y ALGORITHM deben estar configurados en el archivo .env")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña plana coincide con una contraseña hasheada."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashea una contraseña."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crea un token de acceso JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    """Decodifica y valida un token de acceso JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None # Token inválido o expirado