# app/models/user.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, aliased
from typing import List, Optional

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Importa los modelos de asociación
from .user_role import UserRole
from .animal import Animal
from .grupo import Grupo
from .animal_group import AnimalGroup
from .animal_location_history import AnimalLocationHistory
from .health_event import HealthEvent
from .reproductive_event import ReproductiveEvent
from .offspring_born import OffspringBorn
from .weighing import Weighing
from .feeding import Feeding
from .transaction import Transaction
from .batch import Batch
from .product import Product

class User(BaseModel): # Hereda de BaseModel
    __tablename__ = "users"
    # id, created_at, updated_at son heredados de BaseModel

    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    first_name = Column(String)
    last_name = Column(String)
    phone_number = Column(String)
    address = Column(String)
    country = Column(String)
    city = Column(String)

    # Relaciones de seguridad
    user_roles_associations = relationship(
        "UserRole", foreign_keys="[UserRole.user_id]", back_populates="user", cascade="all, delete-orphan"
    )
    assigned_roles = relationship(
        "UserRole", foreign_keys="[UserRole.assigned_by_user_id]", back_populates="assigned_by_user"
    )
    roles = relationship(
        "Role", secondary="user_roles", back_populates="users"
    )

    # Otras relaciones
    farms_owned = relationship("Farm", back_populates="owner_user")
    animals_owned: Mapped[List["Animal"]] = relationship("Animal", back_populates="owner_user")
    farm_accesses = relationship("UserFarmAccess", foreign_keys="[UserFarmAccess.user_id]", back_populates="user")
    accesses_assigned = relationship("UserFarmAccess", foreign_keys="[UserFarmAccess.assigned_by_user_id]", back_populates="assigned_by_user")
    master_data_created = relationship("MasterData", back_populates="created_by_user")
    health_events_administered: Mapped[List["HealthEvent"]] = relationship("HealthEvent", back_populates="administered_by_user")
    reproductive_events_administered: Mapped[List["ReproductiveEvent"]] = relationship("ReproductiveEvent", back_populates="administered_by_user")
    offspring_born: Mapped[List["OffspringBorn"]] = relationship("OffspringBorn", back_populates="born_by_user")
    weighings_recorded: Mapped[List["Weighing"]] = relationship("Weighing", back_populates="recorded_by_user")
    feedings_recorded: Mapped[List["Feeding"]] = relationship("Feeding", back_populates="recorded_by_user")
    transactions_recorded: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="recorded_by_user")
    batches_created: Mapped[List["Batch"]] = relationship("Batch", back_populates="created_by_user")
    products_created: Mapped[List["Product"]] = relationship("Product", back_populates="created_by_user")
    grupos_created: Mapped[List["Grupo"]] = relationship("Grupo", back_populates="created_by_user")
    animal_groups_created: Mapped[List["AnimalGroup"]] = relationship("AnimalGroup", back_populates="created_by_user")
    animal_location_history_created: Mapped[List["AnimalLocationHistory"]] = relationship("AnimalLocationHistory", back_populates="created_by_user")
    # transaction_records_created = relationship("TransactionRecord", back_populates="created_by_user")
    # permissions_assigned = relationship("UserPermission", back_populates="user")
