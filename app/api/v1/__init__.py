# app/api/api_v1/api.py
from fastapi import APIRouter

from app.api.endpoints import (
    users,
    farms,
    lots,
    animals,
    master_data,
    health_events,
    reproductive_events,
    offspring_born,
    weighings,
    feedings,
    transactions,
    batches,
    grupos,
    animal_groups,
    animal_location_history,
    products,
    roles,
    role_permissions,
    user_roles,
    user_farm_access, # <--- AÑADE ESTA LÍNEA
    login, # Asegúrate que tu endpoint de login esté aquí
)

api_router = APIRouter()

# Incluye los routers de los diferentes módulos
api_router.include_router(login.router, tags=["Login"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(farms.router, prefix="/farms", tags=["Farms"])
api_router.include_router(lots.router, prefix="/lots", tags=["Lots"])
api_router.include_router(animals.router, prefix="/animals", tags=["Animals"])
api_router.include_router(master_data.router, prefix="/master_data", tags=["Master Data"])
api_router.include_router(health_events.router, prefix="/health_events", tags=["Health Events"])
api_router.include_router(reproductive_events.router, prefix="/reproductive_events", tags=["Reproductive Events"])
api_router.include_router(offspring_born.router, prefix="/offspring_born", tags=["Offspring Born"])
api_router.include_router(weighings.router, prefix="/weighings", tags=["Weighings"])
api_router.include_router(feedings.router, prefix="/feedings", tags=["Feedings"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(batches.router, prefix="/batches", tags=["Batches"])
api_router.include_router(grupos.router, prefix="/grupos", tags=["Grupos"])
api_router.include_router(animal_groups.router, prefix="/animal_groups", tags=["Animal Groups"])
api_router.include_router(animal_location_history.router, prefix="/animal_location_history", tags=["Animal Location History"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
api_router.include_router(role_permissions.router, prefix="/role_permissions", tags=["Role Permissions"])
api_router.include_router(user_roles.router, prefix="/user_roles", tags=["User Roles"])
api_router.include_router(user_farm_access.router, prefix="/user_farm_access", tags=["User Farm Access"])
