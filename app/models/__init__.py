# app/models/__init__.py
# Este archivo marca 'models' como un paquete.
# Aquí importaremos la Base de SQLAlchemy para que Alembic la detecte
# y, opcionalmente, todos los modelos para que estén disponibles fácilmente.

from app.db.base import Base # Importa la Base para que Alembic la descubra
from app.db.base import BaseModel # Importa BaseModel también si tus modelos heredan de ella directamente

# Importa tus modelos para que sean descubiertos por Alembic y accesibles
from .user import User
from .farm import Farm
from .lot import Lot
from .master_data import MasterData
from .role import Role
from .permission import Permission
from .module import Module
from .role_permission import RolePermission
from .user_role import UserRole
from .animal import Animal
from .grupo import Grupo
from .animal_group import AnimalGroup
from .animal_location_history import AnimalLocationHistory
from .health_event import HealthEvent
from .animal_health_event_pivot import AnimalHealthEventPivot
from .reproductive_event import ReproductiveEvent
from .offspring_born import OffspringBorn
from .weighing import Weighing
from .feeding import Feeding
from .animal_feeding_pivot import AnimalFeedingPivot
from .transaction import Transaction
from .batch import Batch
from .animal_batch_pivot import AnimalBatchPivot
from app.models.product import Product
from .user_farm_access import UserFarmAccess


# Cuando crees otros modelos, impórtalos aquí también:
# from .product import Product
# ... y así sucesivamente para todos tus modelos de BD.
