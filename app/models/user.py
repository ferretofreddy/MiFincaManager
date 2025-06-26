# app/models/user.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, aliased
from typing import List, Optional, ForwardRef

# Importa BaseModel de nuestro módulo app/db/base.py
from app.db.base import BaseModel

# Definiciones de ForwardRef
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
Product = ForwardRef("Product")
Role = ForwardRef("Role") 
UserRole = ForwardRef("UserRole")
UserFarmAccess = ForwardRef("UserFarmAccess")
ConfigurationParameter = ForwardRef("ConfigurationParameter")

class User(BaseModel): # Hereda de BaseModel
    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    phone_number = Column(String)
    address = Column(String)
    country = Column(String)
    city = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # Relaciones ORM
    farms_owned: Mapped[List["Farm"]] = relationship("Farm", back_populates="owner_user")
    animals_owned: Mapped[List["Animal"]] = relationship("Animal", back_populates="owner_user")
    
    farm_accesses: Mapped[List["UserFarmAccess"]] = relationship("UserFarmAccess", foreign_keys="[UserFarmAccess.user_id]", back_populates="user")
    accesses_assigned: Mapped[List["UserFarmAccess"]] = relationship("UserFarmAccess", foreign_keys="[UserFarmAccess.assigned_by_user_id]", back_populates="assigned_by_user")

    master_data_created: Mapped[List["MasterData"]] = relationship("MasterData", back_populates="created_by_user")
    health_events_administered: Mapped[List["HealthEvent"]] = relationship("HealthEvent", back_populates="administered_by_user")
    reproductive_events_administered: Mapped[List["ReproductiveEvent"]] = relationship("ReproductiveEvent", back_populates="administered_by_user")
    offspring_born: Mapped[List["OffspringBorn"]] = relationship("OffspringBorn", back_populates="born_by_user")
    weighings_recorded: Mapped[List["Weighing"]] = relationship("Weighing", back_populates="recorded_by_user")
    feedings_recorded: Mapped[List["Feeding"]] = relationship("Feeding", back_populates="recorded_by_user")
    transactions_recorded: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="recorded_by_user")
    batches_created: Mapped[List["Batch"]] = relationship("Batch", back_populates="created_by_user")
    grupos_created: Mapped[List["Grupo"]] = relationship("Grupo", back_populates="created_by_user")
    animal_groups_created: Mapped[List["AnimalGroup"]] = relationship("AnimalGroup", back_populates="created_by_user")
    animal_location_history_created: Mapped[List["AnimalLocationHistory"]] = relationship("AnimalLocationHistory", back_populates="created_by_user")
    products_created: Mapped[List["Product"]] = relationship("Product", back_populates="created_by_user")
    
    # Relaciones de seguridad (Roles) - ¡CORREGIDAS AQUÍ!
    # Relación Many-to-Many con Role a través de UserRole
    # Esta relación representa LOS ROLES ASIGNADOS A ESTE USUARIO.
    roles_assigned_to_user: Mapped[List["Role"]] = relationship(
        "Role",
        secondary="user_roles", # Nombre de la tabla de asociación
        primaryjoin="User.id == UserRole.user_id", # Cómo User se une a user_roles
        secondaryjoin="Role.id == UserRole.role_id", # Cómo Role se une a user_roles (¡usando role_id!)
        back_populates="users_with_this_role" # Este debe ser el nombre de la relación inversa en Role
    )

    user_roles_associations: Mapped[List["UserRole"]] = relationship(
        "UserRole", 
        foreign_keys="[UserRole.user_id]", 
        back_populates="user",
        overlaps="roles_assigned_to_user,assigned_roles" # Añadido overlaps para evitar warnings
    )
    # assigned_roles es la lista de asociaciones UserRole donde este usuario ES QUIEN ASIGNA
    assigned_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole", 
        foreign_keys="[UserRole.assigned_by_user_id]", 
        back_populates="assigned_by_user",
        overlaps="user_roles_associations" # Añadido overlaps
    )
    
    configuration_parameters_created: Mapped[List["ConfigurationParameter"]] = relationship("ConfigurationParameter", back_populates="created_by_user")
