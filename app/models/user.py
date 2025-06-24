# app/models/user.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, aliased
from typing import List, Optional, ForwardRef

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# No importes los modelos aquí si causan circularidad.
# En su lugar, usa ForwardRef y la referencia en string.
# from .animal import Animal # COMENTAR/ELIMINAR
# from .grupo import Grupo # COMENTAR/ELIMINAR
# ... y así para cualquier otro modelo que tenga relación bidireccional con User

# Definiciones de ForwardRef para los modelos con los que User se relaciona
# y que pueden causar importación circular.
# Solo define aquí los que sean *directamente* referenciados en Mapped[] o relationship()
# y que a su vez puedan importar User.
Animal = ForwardRef("Animal")
Farm = ForwardRef("Farm")
MasterData = ForwardRef("MasterData")
HealthEvent = ForwardRef("HealthEvent")
ReproductiveEvent = ForwardRef("ReproductiveEvent")
OffspringBorn = ForwardRef("OffspringBorn")
Weighing = ForwardRef("Weighing")
Feeding = ForwardRef("Feeding")
Transaction = ForwardRef("Transaction")
Batch = ForwardRef("Batch")
Grupo = ForwardRef("Grupo")
AnimalGroup = ForwardRef("AnimalGroup")
AnimalLocationHistory = ForwardRef("AnimalLocationHistory")
Product = ForwardRef("Product") # Para la nueva relación products_created
UserFarmAccess = ForwardRef("UserFarmAccess") # <--- AÑADE ESTA LÍNEA

# Importa solo los modelos de asociación que no causen circularidad directa
from .user_role import UserRole
# Si UserFarmAccess no causa circularidad, mantener la importación directa.
# Si causa, también poner en ForwardRef. Asumo que está bien por ahora.
# from .user_farm_access import UserFarmAccess # <--- ¡COMENTA O ELIMINA ESTA LÍNEA AQUÍ!


class User(BaseModel):
    __tablename__ = "users"

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
    user_roles_associations: Mapped[List["UserRole"]] = relationship(
        "UserRole", foreign_keys="[UserRole.user_id]", back_populates="user", cascade="all, delete-orphan"
    )
    assigned_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole", foreign_keys="[UserRole.assigned_by_user_id]", back_populates="assigned_by_user"
    )
    roles: Mapped[List["Role"]] = relationship(
        "Role", secondary="user_roles", back_populates="users"
    )

    # Otras relaciones - USANDO REFERENCIAS DE STRING O FORWARDREF
    farms_owned: Mapped[List["Farm"]] = relationship(Farm, back_populates="owner_user")
    animals_owned: Mapped[List["Animal"]] = relationship(Animal, back_populates="owner_user")
    farm_accesses: Mapped[List["UserFarmAccess"]] = relationship(UserFarmAccess, foreign_keys="[UserFarmAccess.user_id]", back_populates="user")
    accesses_assigned: Mapped[List["UserFarmAccess"]] = relationship(UserFarmAccess, foreign_keys="[UserFarmAccess.assigned_by_user_id]", back_populates="assigned_by_user")
    master_data_created: Mapped[List["MasterData"]] = relationship(MasterData, back_populates="created_by_user")
    health_events_administered: Mapped[List["HealthEvent"]] = relationship(HealthEvent, back_populates="administered_by_user")
    reproductive_events_administered: Mapped[List["ReproductiveEvent"]] = relationship(ReproductiveEvent, back_populates="administered_by_user")
    offspring_born: Mapped[List["OffspringBorn"]] = relationship(OffspringBorn, back_populates="born_by_user")
    weighings_recorded: Mapped[List["Weighing"]] = relationship(Weighing, back_populates="recorded_by_user")
    feedings_recorded: Mapped[List["Feeding"]] = relationship(Feeding, back_populates="recorded_by_user")
    transactions_recorded: Mapped[List["Transaction"]] = relationship(Transaction, back_populates="recorded_by_user")
    batches_created: Mapped[List["Batch"]] = relationship(Batch, back_populates="created_by_user")
    grupos_created: Mapped[List["Grupo"]] = relationship(Grupo, back_populates="created_by_user")
    animal_groups_created: Mapped[List["AnimalGroup"]] = relationship(AnimalGroup, back_populates="created_by_user")
    animal_location_history_created: Mapped[List["AnimalLocationHistory"]] = relationship(AnimalLocationHistory, back_populates="created_by_user")
    products_created: Mapped[List["Product"]] = relationship(Product, back_populates="created_by_user")
