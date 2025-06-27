# app/api/v1/__init__.py
from fastapi import APIRouter

# Importa los routers individuales desde la carpeta 'endpoints'.
# Cada archivo (ej. users.py, farms.py) debería tener una instancia de APIRouter llamada 'router'.
from .endpoints.users import router as users_router
from .endpoints.farms import router as farms_router
from .endpoints.lots import router as lots_router
from .endpoints.animals import router as animals_router
from .endpoints.master_data import router as master_data_router
from .endpoints.health_event import router as health_events_router
from .endpoints.reproductive_event import router as reproductive_events_router
from .endpoints.offspring_born import router as offspring_born_router
from .endpoints.weighing import router as weighings_router
from .endpoints.feeding import router as feedings_router
from .endpoints.transaction import router as transactions_router
from .endpoints.batch import router as batches_router
from .endpoints.grupo import router as grupos_router
from .endpoints.animal_group import router as animal_groups_router
from .endpoints.animal_location_history import router as animal_location_history_router
from .endpoints.products import router as products_router
from .endpoints.roles import router as roles_router
from .endpoints.permissions import router as permissions_router
from .endpoints.role_permissions import router as role_permissions_router # Asumiendo que tendrás un router para esto
from .endpoints.user_roles import router as user_roles_router # Asumiendo que tendrás un router para esto
from .endpoints.user_farm_access import router as user_farm_access_router # Asumiendo que tendrás un router para esto
from .endpoints.configuration_parameters import router as configuration_parameters_router # Asumiendo que tendrás un router para esto
from .endpoints.auth import router as auth_router # Router para autenticación/login (asumiendo que crearás este archivo)


api_router = APIRouter()

# Incluye los routers de los diferentes módulos
api_router.include_router(auth_router, tags=["Auth"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(farms_router, prefix="/farms", tags=["Farms"])
api_router.include_router(lots_router, prefix="/lots", tags=["Lots"])
api_router.include_router(animals_router, prefix="/animals", tags=["Animals"])
api_router.include_router(master_data_router, prefix="/master_data", tags=["Master Data"])
api_router.include_router(health_events_router, prefix="/health_events", tags=["Health Events"])
api_router.include_router(reproductive_events_router, prefix="/reproductive_events", tags=["Reproductive Events"])
api_router.include_router(offspring_born_router, prefix="/offspring_born", tags=["Offspring Born"])
api_router.include_router(weighings_router, prefix="/weighings", tags=["Weighings"])
api_router.include_router(feedings_router, prefix="/feedings", tags=["Feedings"])
api_router.include_router(transactions_router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(batches_router, prefix="/batches", tags=["Batches"])
api_router.include_router(grupos_router, prefix="/grupos", tags=["Grupos"])
api_router.include_router(animal_groups_router, prefix="/animal_groups", tags=["Animal Groups"])
api_router.include_router(animal_location_history_router, prefix="/animal_location_history", tags=["Animal Location History"])
api_router.include_router(products_router, prefix="/products", tags=["Products"])
api_router.include_router(roles_router, prefix="/roles", tags=["Roles"])
api_router.include_router(permissions_router, prefix="/permissions", tags=["Permissions"])
api_router.include_router(role_permissions_router, prefix="/role_permissions", tags=["Role Permissions"])
api_router.include_router(user_roles_router, prefix="/user_roles", tags=["User Roles"])
api_router.include_router(user_farm_access_router, prefix="/user_farm_access", tags=["User Farm Access"])
api_router.include_router(configuration_parameters_router, prefix="/configuration_parameters", tags=["Configuration Parameters"])

