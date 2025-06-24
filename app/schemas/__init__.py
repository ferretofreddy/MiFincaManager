# app/schemas/__init__.py
# Este archivo marca 'schemas' como un paquete.
# Aquí importaremos los esquemas de Pydantic para un acceso centralizado si se desea.

from .user import User, UserCreate, UserUpdate, UserReduced
from .farm import Farm, FarmCreate, FarmUpdate, FarmReduced
from .lot import Lot, LotCreate, LotUpdate, LotReduced
from .master_data import MasterData, MasterDataCreate, MasterDataUpdate, MasterDataReduced
from .role import Role, RoleCreate, RoleUpdate, RoleReduced
from .permission import Permission, PermissionCreate, PermissionUpdate, PermissionReduced
from .module import Module, ModuleCreate, ModuleUpdate, ModuleReduced
from .role_permission import RolePermission, RolePermissionCreate
from .user_role import UserRole, UserRoleCreate
from .animal import Animal, AnimalCreate, AnimalUpdate, AnimalReduced, AnimalReducedForAnimalGroup, AnimalReducedForUser
from .grupo import Grupo, GrupoCreate, GrupoUpdate, GrupoReduced, GrupoReducedForAnimalGroup
from .animal_group import AnimalGroup, AnimalGroupCreate, AnimalGroupUpdate, AnimalGroupReduced, AnimalGroupReducedForAnimal, AnimalGroupReducedForGrupo
from .animal_location_history import AnimalLocationHistory, AnimalLocationHistoryCreate, AnimalLocationHistoryUpdate, AnimalLocationHistoryReduced, AnimalLocationHistoryReducedForAnimal, AnimalLocationHistoryReducedForLot
from .health_event import HealthEvent, HealthEventCreate, HealthEventUpdate, HealthEventReduced, HealthEventReducedForPivot
from .animal_health_event_pivot import AnimalHealthEventPivot, AnimalHealthEventPivotCreate, AnimalHealthEventPivotReduced, AnimalHealthEventPivotReducedForAnimal, AnimalHealthEventPivotReducedForHealthEvent
from .reproductive_event import ReproductiveEvent, ReproductiveEventCreate, ReproductiveEventUpdate, ReproductiveEventReduced, ReproductiveEventReducedForOffspringBorn
from .offspring_born import OffspringBorn, OffspringBornCreate, OffspringBornUpdate, OffspringBornReduced
from .weighing import Weighing, WeighingCreate, WeighingUpdate, WeighingReduced
from .feeding import Feeding, FeedingCreate, FeedingUpdate, FeedingReduced
from .animal_feeding_pivot import AnimalFeedingPivot, AnimalFeedingPivotCreate, AnimalFeedingPivotReduced
from .transaction import Transaction, TransactionCreate, TransactionUpdate, TransactionReduced
from .batch import Batch, BatchCreate, BatchUpdate, BatchReduced # ¡Nuevo! Importa los schemas de Batch
from .animal_batch_pivot import AnimalBatchPivot, AnimalBatchPivotCreate, AnimalBatchPivotReduced # ¡Nuevo! Importa los schemas de AnimalBatchPivot
from .product import Product, ProductCreate, ProductUpdate, ProductReduced # ¡NUEVO! Importa los schemas de Product
# Cuando crees otros schemas, impórtalos aquí también:
# from .product import Product, ProductCreate, ProductUpdate, ProductReduced
# ... y así sucesivamente para todos tus schemas.
