# main.py
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import os

# Importa las funciones y clases necesarias de la base de datos
from app.db.base import Base # Asume que Base se define en app/db/base.py
from app.db.session import engine, get_db # Importa engine y get_db de app/db/session.py
from app.core.config import settings # Importa la configuración centralizada

# Importa los routers de tus endpoints. Asegúrate de que existan o los crearás.
# Solo importaremos los que tenemos en los modelos, y luego agregaremos los de seguridad.
from app.api.v1.endpoints import (
    users, master_data, farms, animals, grupo, animal_group,
    animal_location_history, health_event, reproductive_event,
    offspring_born, weighing, feeding, transaction, batch,
    products, roles, permissions,
    configuration_parameters,
    user_farm_access,
    user_roles,
    auth # Router para autenticación y manejo de tokens
)

# Configuración de FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME, # Usa el nombre del proyecto de la configuración
    description="API para la gestión integral de fincas ganaderas. Incluye gestión de usuarios, granjas, animales y eventos.",
    version="1.0.0",
    docs_url="/api/docs", # Ruta para la documentación interactiva (Swagger UI)
    redoc_url="/api/redoc", # Ruta para la documentación alternativa (ReDoc)
    openapi_url="/api/openapi.json" # Ruta para el esquema OpenAPI
)

# Configuración de CORS (Cross-Origin Resource Sharing)
# Esto permite que tu frontend (ej. localhost:3000) acceda a tu backend.
origins = [
    "http://localhost",
    "http://localhost:3000", # Reemplaza con la URL de tu frontend si es diferente
    "http://127.0.0.1:3000",
    # Puedes añadir más orígenes si tu frontend se aloja en otros dominios
    # "https://your-frontend-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permite todos los métodos (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Permite todos los headers
)

# Eventos de inicio y apagado de la aplicación (hooks)
@app.on_event("startup")
async def startup_event():
    """Evento que se ejecuta al iniciar la aplicación."""
    print("Aplicación MiFincaManager iniciando...")
    # Puedes añadir lógica de inicialización aquí si es necesario,
    # como la precarga de datos maestros o la comprobación de conexión a la DB.
    # La función run_migrations se ha movido fuera de aquí ya que es mejor
    # ejecutar las migraciones manualmente o con un script de despliegue.
    pass

@app.on_event("shutdown")
async def shutdown_event():
    """Evento que se ejecuta al apagar la aplicación."""
    print("Aplicación MiFincaManager apagándose...")
    # Puedes añadir lógica de limpieza aquí, como cerrar conexiones o liberar recursos.


# Incluir los routers en la aplicación FastAPI
# Prefijo de API para todos los endpoints (usando settings.API_V1_STR)
API_PREFIX = settings.API_V1_STR

# Se asume que cada archivo de endpoint (ej. users.py) tiene una variable 'router' de tipo APIRouter.
app.include_router(users.router, prefix=API_PREFIX, tags=["Users"])
app.include_router(farms.router, prefix=API_PREFIX, tags=["Farms"])
app.include_router(animals.router, prefix=API_PREFIX, tags=["Animals"])
app.include_router(master_data.router, prefix=API_PREFIX, tags=["Master Data"])
app.include_router(lots.router, prefix=API_PREFIX, tags=["Lots"])
app.include_router(grupos.router, prefix=API_PREFIX, tags=["Grupos"])
app.include_router(animal_group.router, prefix=API_PREFIX, tags=["Animal Groups"])
app.include_router(animal_location_history.router, prefix=API_PREFIX, tags=["Animal Location History"])
app.include_router(health_event.router, prefix=API_PREFIX, tags=["Health Events"])
app.include_router(reproductive_event.router, prefix=API_PREFIX, tags=["Reproductive Events"])
app.include_router(offspring_born.router, prefix=API_PREFIX, tags=["Offspring Born"])
app.include_router(weighings.router, prefix=API_PREFIX, tags=["Weighings"])
app.include_router(feedings.router, prefix=API_PREFIX, tags=["Feedings"])
app.include_router(transactions.router, prefix=API_PREFIX, tags=["Transactions"])
app.include_router(batch.router, prefix=API_PREFIX, tags=["Batches"])
app.include_router(products.router, prefix=API_PREFIX, tags=["Products"])
app.include_router(roles.router, prefix=API_PREFIX, tags=["Roles"])
app.include_router(permissions.router, prefix=API_PREFIX, tags=["Permissions"])
app.include_router(configuration_parameters.router, prefix=API_PREFIX, tags=["Configuration Parameters"])
app.include_router(user_farm_access.router, prefix=API_PREFIX, tags=["User Farm Access"])
app.include_router(user_roles.router, prefix=API_PREFIX, tags=["User Roles"])

# Router de autenticación (lo crearemos a continuación)
app.include_router(auth.router, prefix=API_PREFIX, tags=["Auth"])

# Ruta raíz para verificar que la API está funcionando
@app.get("/")
async def read_root():
    return {"message": "Welcome to MiFincaManager API! Visit /api/docs for documentation."}

