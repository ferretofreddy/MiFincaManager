# models.py
from sqlalchemy import Column, String, UUID, TIMESTAMP, DECIMAL, Date, Text, Boolean, ForeignKey, UniqueConstraint, Integer, Index 
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM, JSONB # Importa ENUM de postgresql para Column
from datetime import datetime
import uuid

from database import Base
from app_enums import ( # Importa los nuevos ENUMS de Python
    SexEnumPython, AnimalStatusEnumPython, AnimalOriginEnumPython, HealthEventTypeEnumPython,
    ReproductiveEventTypeEnumPython, GestationDiagnosisResultEnumPython, TransactionTypeEnumPython,
    ParamDataTypeEnumPython
)

# --- Definición de ENUMS personalizados para SQLAlchemy ---
# Usamos `values_callable` para mapear los valores de string de DB a los miembros de Python Enum
# `create_type=False` porque asumimos que los tipos ENUM ya existen en la DB.
SexEnum = ENUM(SexEnumPython, values_callable=lambda obj: [e.value for e in obj], name='sex_enum', create_type=False)
AnimalStatusEnum = ENUM(AnimalStatusEnumPython, values_callable=lambda obj: [e.value for e in obj], name='animal_status_enum', create_type=False)
AnimalOriginEnum = ENUM(AnimalOriginEnumPython, values_callable=lambda obj: [e.value for e in obj], name='animal_origin_enum', create_type=False)
HealthEventTypeEnum = ENUM(HealthEventTypeEnumPython, values_callable=lambda obj: [e.value for e in obj], name='health_event_type_enum', create_type=False)
ReproductiveEventTypeEnum = ENUM(ReproductiveEventTypeEnumPython, values_callable=lambda obj: [e.value for e in obj], name='reproductive_event_type_enum', create_type=False)
GestationDiagnosisResultEnum = ENUM(GestationDiagnosisResultEnumPython, values_callable=lambda obj: [e.value for e in obj], name='gestation_diagnosis_result_enum', create_type=False)
TransactionTypeEnum = ENUM(TransactionTypeEnumPython, values_callable=lambda obj: [e.value for e in obj], name='transaction_type_enum', create_type=False)
ParamDataTypeEnum = ENUM(ParamDataTypeEnumPython, values_callable=lambda obj: [e.value for e in obj], name='param_data_type_enum', create_type=False)


# 1. User Model
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone_number = Column(String(20))
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now, onupdate=datetime.now)

    # Relaciones para User (como entidad principal)
    roles = relationship("UserRole", back_populates="user", lazy="selectin") 
    farms_owned = relationship("Farm", back_populates="owner_user", lazy="selectin")
    animals_owned = relationship("Animal", back_populates="owner_user", lazy="selectin")
    
    farm_accesses = relationship("UserFarmAccess", foreign_keys="[UserFarmAccess.user_id]", back_populates="user", lazy="selectin")
    accesses_assigned = relationship("UserFarmAccess", foreign_keys="[UserFarmAccess.assigned_by_user_id]", back_populates="assigned_by_user", lazy="selectin")

    master_data_created = relationship("MasterData", back_populates="created_by_user", lazy="selectin")
    health_events_administered = relationship("HealthEvent", back_populates="administered_by_user", lazy="selectin")
    feedings_administered = relationship("Feeding", back_populates="administered_by_user", lazy="selectin")
    config_params_updated = relationship("ConfigurationParameter", back_populates="last_updated_by_user", lazy="selectin")
    
    transactions_from_owner = relationship("Transaction", foreign_keys="[Transaction.from_owner_user_id]", back_populates="from_owner_user", lazy="selectin")
    transactions_to_owner = relationship("Transaction", foreign_keys="[Transaction.to_owner_user_id]", back_populates="to_owner_user", lazy="selectin")

    role_permissions_granted = relationship("RolePermission", foreign_keys="[RolePermission.granted_by_user_id]", back_populates="granted_by_user", lazy="selectin")

    # Nueva relación para Grupos creados por este usuario
    grupos_created = relationship("Grupo", back_populates="created_by_user", lazy="selectin")

    __table_args__ = (
        Index('idx_users_email', email),
    )


# 2. Role Model
class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)

    permissions = relationship("RolePermission", back_populates="role", lazy="selectin") 
    user_roles = relationship("UserRole", back_populates="role", lazy="selectin") 


# 3. UserRole Model (Association table)
class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)
    assigned_at = Column(TIMESTAMP(timezone=True), default=datetime.now)

    user = relationship("User", back_populates="roles", lazy="selectin") 
    role = relationship("Role", back_populates="user_roles", lazy="selectin") 


# 4. Module Model
class Module(Base):
    __tablename__ = "modules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)

    permissions = relationship("Permission", back_populates="module", lazy="selectin")


# 5. Permission Model
class Permission(Base):
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    module_id = Column(UUID(as_uuid=True), ForeignKey("modules.id"))

    module = relationship("Module", back_populates="permissions", lazy="selectin") 
    permissions_in_roles = relationship("RolePermission", back_populates="permission", lazy="selectin")


# 6. RolePermission Model (Association table)
class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True)
    granted_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    granted_at = Column(TIMESTAMP(timezone=True), default=datetime.now)

    role = relationship("Role", back_populates="permissions", lazy="selectin")
    permission = relationship("Permission", back_populates="permissions_in_roles", lazy="selectin")
    granted_by_user = relationship("User", foreign_keys=[granted_by_user_id], back_populates="role_permissions_granted", lazy="selectin")


# 7. Farm Model
class Farm(Base):
    __tablename__ = "farms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    location = Column(String(255))
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    area_hectares = Column(DECIMAL(10, 2))
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    contact_info = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now) 
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now, onupdate=datetime.now)

    owner_user = relationship("User", back_populates="farms_owned", lazy="selectin")
    user_accesses = relationship("UserFarmAccess", back_populates="farm", lazy="selectin")
    lots = relationship("Lot", back_populates="farm", lazy="selectin")

    __table_args__ = (
        Index('idx_farms_owner_user_id', owner_user_id),
    )


# 8. UserFarmAccess Model (Association table for shared farm access)
class UserFarmAccess(Base):
    __tablename__ = "user_farm_access"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"), primary_key=True)
    assigned_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    assigned_at = Column(TIMESTAMP(timezone=True), default=datetime.now)
    expires_at = Column(TIMESTAMP(timezone=True))

    user = relationship("User", foreign_keys=[user_id], back_populates="farm_accesses", lazy="selectin")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by_user_id], back_populates="accesses_assigned", lazy="selectin")
    farm = relationship("Farm", back_populates="user_accesses", lazy="selectin")

    __table_args__ = (
        UniqueConstraint('user_id', 'farm_id', name='unique_user_farm_access'),
        Index('idx_user_farm_access_user_id', user_id),
        Index('idx_user_farm_access_farm_id', farm_id),
    )


# 10. Lot Model (Physical Section of a Farm)
class Lot(Base):
    __tablename__ = "lots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now, onupdate=datetime.now)

    farm = relationship("Farm", back_populates="lots", lazy="selectin")
    animals = relationship("Animal", back_populates="current_lot", lazy="selectin")

    __table_args__ = (
        UniqueConstraint('farm_id', 'name', name='unique_lot_name_per_farm'),
    )


# 20. MasterData Model (used for species, breed, group purpose etc.)
class MasterData(Base):
    __tablename__ = "master_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    category = Column(String(100), nullable=False) 
    name = Column(String(255), nullable=False)
    description = Column(Text)
    properties = Column(JSONB) 
    is_active = Column(Boolean, default=True)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now, onupdate=datetime.now)

    created_by_user = relationship("User", foreign_keys=[created_by_user_id], back_populates="master_data_created", lazy="selectin")
    # Nueva relación para Grupos, si MasterData se usa para definir propósitos de grupo
    grupo_purposes = relationship("Grupo", back_populates="purpose", lazy="selectin")

    __table_args__ = (
        UniqueConstraint('category', 'name', name='unique_master_data_name_per_category'),
        Index('idx_master_data_category', category),
    )

# NUEVO: 22. Grupo Model (Dynamic Animal Group for Events/Procedures)
class Grupo(Base):
    __tablename__ = "grupos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False) # E.g., "Grupo Desparasitación Junio 2025"
    description = Column(Text)
    purpose_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id")) # FK to MasterData (category='group_purpose')
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now, onupdate=datetime.now)

    purpose = relationship("MasterData", foreign_keys=[purpose_id], back_populates="grupo_purposes", lazy="selectin")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id], back_populates="grupos_created", lazy="selectin")
    animals_in_group = relationship("AnimalGroup", back_populates="grupo", lazy="selectin") 

    __table_args__ = (
        Index('idx_grupos_purpose_id', purpose_id),
        Index('idx_grupos_created_by_user_id', created_by_user_id),
    )


# NUEVO: 23. AnimalGroup Model (Association table for Animal <-> Grupo)
class AnimalGroup(Base):
    __tablename__ = "animal_groups"

    animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), primary_key=True)
    grupo_id = Column(UUID(as_uuid=True), ForeignKey("grupos.id"), primary_key=True)
    assigned_date = Column(Date, nullable=False, default=datetime.now().date())
    removed_date = Column(Date) # Fecha opcional de remoción del grupo
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now) # Para auditoría de la asignación

    animal = relationship("Animal", back_populates="groups_history", lazy="selectin")
    grupo = relationship("Grupo", back_populates="animals_in_group", lazy="selectin")

    __table_args__ = (
        UniqueConstraint('animal_id', 'grupo_id', name='unique_animal_group_assignment'),
        Index('idx_animal_groups_animal_id', animal_id),
        Index('idx_animal_groups_grupo_id', grupo_id),
    )


# 9. Animal Model (Existing - adding groups_history relationship)
class Animal(Base):
    __tablename__ = "animals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    tag_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100))
    species_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"))
    breed_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"))
    sex = Column(SexEnum, nullable=False) 
    date_of_birth = Column(Date)
    current_status = Column(AnimalStatusEnum, nullable=False) 
    origin = Column(AnimalOriginEnum, nullable=False) 
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    mother_animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"))
    father_animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"))
    description = Column(Text)
    photo_url = Column(String(255))
    current_lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id")) 
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now, onupdate=datetime.now)

    owner_user = relationship("User", back_populates="animals_owned", lazy="selectin")
    species = relationship("MasterData", foreign_keys=[species_id], lazy="selectin")
    breed = relationship("MasterData", foreign_keys=[breed_id], lazy="selectin")
    current_lot = relationship("Lot", back_populates="animals", lazy="selectin") 

    # Self-referencing relationships (mother/father)
    mother = relationship("Animal", remote_side=[id], foreign_keys=[mother_animal_id], backref="offspring_mother_animal", lazy="selectin")
    father = relationship("Animal", remote_side=[id], foreign_keys=[father_animal_id], backref="offspring_father_animal", lazy="selectin")
    
    locations_history = relationship("AnimalLocationHistory", back_populates="animal", lazy="selectin")
    health_events_pivot = relationship("AnimalHealthEventPivot", back_populates="animal", lazy="selectin")
    
    # ReproductiveEvent tiene dos FKs a Animal: animal_id y sire_animal_id
    # Esta relación es para cuando el animal es la HEMBRA en el evento reproductivo
    reproductive_events = relationship("ReproductiveEvent", foreign_keys="[ReproductiveEvent.animal_id]", back_populates="animal", lazy="selectin")
    # Nueva relación para cuando el animal es el SEMENTAL en un evento reproductivo
    sire_reproductive_events = relationship("ReproductiveEvent", foreign_keys="[ReproductiveEvent.sire_animal_id]", back_populates="sire_animal", lazy="selectin")
    
    weighings = relationship("Weighing", back_populates="animal", lazy="selectin")
    feedings_pivot = relationship("AnimalFeedingPivot", back_populates="animal", lazy="selectin")
    transactions = relationship("Transaction", back_populates="animal", lazy="selectin")
    offspring_born_events = relationship("OffspringBorn", foreign_keys='[OffspringBorn.offspring_animal_id]', back_populates="offspring_animal", lazy="selectin")
    
    # Nueva relación para grupos a los que pertenece el animal
    groups_history = relationship("AnimalGroup", back_populates="animal", lazy="selectin")

    __table_args__ = (
        Index('idx_animals_tag_id', tag_id),
        Index('idx_animals_owner_user_id', owner_user_id),
        Index('idx_animals_current_lot_id', current_lot_id),
    )


# 11. AnimalLocationHistory Model
class AnimalLocationHistory(Base):
    __tablename__ = "animal_locations_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), nullable=False)
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    entry_date = Column(Date, nullable=False)
    exit_date = Column(Date)
    reason = Column(String(100))
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now)

    animal = relationship("Animal", back_populates="locations_history", lazy="selectin") 
    farm = relationship("Farm", foreign_keys=[farm_id], lazy="selectin") 

    __table_args__ = (
        UniqueConstraint('animal_id', 'farm_id', 'entry_date', name='unique_animal_location_entry'), 
        Index('idx_animal_locations_history_animal_id', animal_id),
        Index('idx_animal_locations_history_farm_id', farm_id),
    )


# 12. HealthEvent Model
class HealthEvent(Base):
    __tablename__ = "health_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(HealthEventTypeEnum, nullable=False) 
    event_date = Column(Date, nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"))
    dosage = Column(String(100))
    administered_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    diagnosis = Column(Text)
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now)

    product = relationship("MasterData", foreign_keys=[product_id], lazy="selectin")
    administered_by_user = relationship("User", foreign_keys=[administered_by_user_id], back_populates="health_events_administered", lazy="selectin")
    animals_affected = relationship("AnimalHealthEventPivot", back_populates="health_event", lazy="selectin")

    __table_args__ = (
        Index('idx_health_events_event_date', event_date),
    )


# 13. AnimalHealthEventPivot Model (Association table)
class AnimalHealthEventPivot(Base):
    __tablename__ = "animal_health_event_pivot"

    health_event_id = Column(UUID(as_uuid=True), ForeignKey("health_events.id"), primary_key=True)
    animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), primary_key=True)

    health_event = relationship("HealthEvent", back_populates="animals_affected", lazy="selectin")
    animal = relationship("Animal", back_populates="health_events_pivot", lazy="selectin")


# 14. ReproductiveEvent Model
class ReproductiveEvent(Base):
    __tablename__ = "reproductive_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), nullable=False) 
    event_type = Column(ReproductiveEventTypeEnum, nullable=False) 
    event_date = Column(Date, nullable=False)
    sire_animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id")) 
    gestation_diagnosis_result = Column(GestationDiagnosisResultEnum) 
    expected_delivery_date = Column(Date)
    actual_delivery_date = Column(Date)
    number_of_offspring = Column(Integer)
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now)

    animal = relationship("Animal", foreign_keys=[animal_id], back_populates="reproductive_events", lazy="selectin")
    sire_animal = relationship("Animal", foreign_keys=[sire_animal_id], back_populates="sire_reproductive_events", lazy="selectin")
    offspring = relationship("OffspringBorn", back_populates="reproductive_event", lazy="selectin")

    __table_args__ = (
        Index('idx_reproductive_events_animal_id', animal_id),
        Index('idx_reproductive_events_sire_animal_id', sire_animal_id),
    )


# 15. OffspringBorn Model
class OffspringBorn(Base):
    __tablename__ = "offspring_born"

    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    reproductive_event_id = Column(UUID(as_uuid=True), ForeignKey("reproductive_events.id"), nullable=False)
    offspring_animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now)

    reproductive_event = relationship("ReproductiveEvent", back_populates="offspring", lazy="selectin")
    offspring_animal = relationship("Animal", foreign_keys=[offspring_animal_id], back_populates="offspring_born_events", lazy="selectin")

    __table_args__ = (
        UniqueConstraint('reproductive_event_id', 'offspring_animal_id', name='unique_offspring_assignment'),
        Index('idx_offspring_born_reproductive_event_id', reproductive_event_id),
        Index('idx_offspring_born_offspring_animal_id', offspring_animal_id),
    )


# 16. Weighing Model
class Weighing(Base):
    __tablename__ = "weighings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), nullable=False)
    weighing_date = Column(Date, nullable=False)
    weight_kg = Column(DECIMAL(8, 2), nullable=False)
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now)

    animal = relationship("Animal", back_populates="weighings", lazy="selectin")

    __table_args__ = (
        Index('idx_weighings_animal_id', animal_id),
    )


# 17. Feeding Model
class Feeding(Base):
    __tablename__ = "feedings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    feeding_date = Column(Date, nullable=False)
    feed_type_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"), nullable=False)
    quantity_kg = Column(DECIMAL(8, 2), nullable=False)
    supplement_id = Column(UUID(as_uuid=True), ForeignKey("master_data.id"))
    administered_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now)

    feed_type = relationship("MasterData", foreign_keys=[feed_type_id], lazy="selectin")
    supplement = relationship("MasterData", foreign_keys=[supplement_id], lazy="selectin")
    administered_by_user = relationship("User", foreign_keys=[administered_by_user_id], back_populates="feedings_administered", lazy="selectin")
    animals_fed = relationship("AnimalFeedingPivot", back_populates="feeding", lazy="selectin")

    __table_args__ = (
        Index('idx_feedings_feeding_date', feeding_date),
        Index('idx_feedings_feed_type_id', feed_type_id),
    )


# 18. AnimalFeedingPivot Model (Association table)
class AnimalFeedingPivot(Base):
    __tablename__ = "animal_feeding_pivot"

    feeding_id = Column(UUID(as_uuid=True), ForeignKey("feedings.id"), primary_key=True)
    animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), primary_key=True)

    feeding = relationship("Feeding", back_populates="animals_fed", lazy="selectin")
    animal = relationship("Animal", back_populates="feedings_pivot", lazy="selectin")


# 19. Transaction Model
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_type = Column(TransactionTypeEnum, nullable=False) 
    transaction_date = Column(Date, nullable=False)
    animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), nullable=False)
    from_farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"))
    to_farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"))
    from_owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    to_owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    price_value = Column(DECIMAL(12, 2))
    reason_for_movement = Column(Text)
    transport_info = Column(Text) 
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now)

    animal = relationship("Animal", back_populates="transactions", lazy="selectin")
    from_farm = relationship("Farm", foreign_keys=[from_farm_id], lazy="selectin")
    to_farm = relationship("Farm", foreign_keys=[to_farm_id], lazy="selectin")
    from_owner_user = relationship("User", foreign_keys=[from_owner_user_id], back_populates="transactions_from_owner", lazy="selectin")
    to_owner_user = relationship("User", foreign_keys=[to_owner_user_id], back_populates="transactions_to_owner", lazy="selectin") 

    __table_args__ = (
        Index('idx_transactions_animal_id', animal_id),
        Index('idx_transactions_transaction_date', transaction_date),
    )


# 21. ConfigurationParameter Model
class ConfigurationParameter(Base):
    __tablename__ = "configuration_parameters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    parameter_name = Column(String(100), unique=True, nullable=False)
    parameter_value = Column(String(255), nullable=False)
    data_type = Column(ParamDataTypeEnum, nullable=False) 
    description = Column(Text)
    last_updated_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now, onupdate=datetime.now)

    last_updated_by_user = relationship("User", foreign_keys=[last_updated_by_user_id], back_populates="config_params_updated", lazy="selectin")
