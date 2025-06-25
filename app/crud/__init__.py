# app/crud/__init__.py
# Este archivo marca 'crud' como un paquete.
# Aquí importamos las instancias de CRUD de cada modelo
# para un acceso fácil desde otras partes de la aplicación.

from .base import CRUDBase
from .user import user
from .farm import farm
from .animal import animal
from .lot import lot
from .master_data import master_data
from .grupo import grupo
from .health_events import health_event
from .reproductive_events import reproductive_event
from .offspring_born import offspring_born
from .weighings import weighing
from .feedings import feeding
from .batch import batch
from .transaction import transaction
from .animal_group import animal_group

# CRUDs de seguridad
from .module import module
from .permission import permission
from .role import role
from .role_permissions import role_permission
from .user_roles import user_role


# Últimos CRUDs
from .products import product
from .user_farm_access import user_farm_access
from .animal_batch_pivot import animal_batch_pivot
from .animal_feeding_pivot import animal_feeding_pivot
from .animal_health_event_pivot import animal_health_event_pivot
from .animal_location_history import animal_location_history

# Cuando crees otros módulos CRUD, impórtalos aquí también:
# from .products import product as product_crud
# ... y así sucesivamente.
