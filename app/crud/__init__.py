# app/crud/__init__.py
# Este archivo marca 'crud' como un paquete.
# Aquí importamos las instancias de CRUD de cada modelo
# para un acceso fácil desde otras partes de la aplicación.

from .users import user as user_crud
from .farms import farm as farm_crud
from .lots import lot as lot_crud
from .master_data import master_data as master_data_crud
from .roles import role as role_crud
from .permissions import permission as permission_crud
from .modules import module as module_crud
from .role_permissions import role_permission as role_permission_crud
from .user_roles import user_role as user_role_crud
from .animals import animal as animal_crud
from .grupos import grupo as grupo_crud
from .animal_groups import animal_group as animal_group_crud
from .animal_location_history import animal_location_history as animal_location_history_crud
from .health_events import health_event as health_event_crud
from .animal_health_event_pivot import animal_health_event_pivot as animal_health_event_pivot_crud
from .reproductive_events import reproductive_event as reproductive_event_crud
from .offspring_born import offspring_born as offspring_born_crud
from .weighings import weighing as weighing_crud
from .feedings import feeding as feeding_crud
from .animal_feeding_pivot import animal_feeding_pivot as animal_feeding_pivot_crud
from .transactions import transaction as transaction_crud
from .batches import batch as batch_crud # ¡Nuevo! Importa la instancia de CRUD para Batch
from .animal_batch_pivot import animal_batch_pivot as animal_batch_pivot_crud # ¡Nuevo! Importa la instancia de CRUD para AnimalBatchPivot
from .products import product as product_crud # ¡NUEVO! Importa la instancia de CRUD para Product

# Cuando crees otros módulos CRUD, impórtalos aquí también:
# from .products import product as product_crud
# ... y así sucesivamente.
