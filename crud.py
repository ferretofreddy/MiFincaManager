# crud.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import select, func, or_, delete
from datetime import datetime, date
import uuid
from typing import List, Optional # Mantener List si hay necesidad para Python < 3.9 o eliminar si solo se usa 'list'

import models
import schemas
from app_security import get_password_hash # Importa get_password_hash para crear usuarios

# Funciones CRUD para User
async def get_user_by_email(db: AsyncSession, email: str):
    """Obtiene un usuario por su email."""
    result = await db.execute(select(models.User).filter(models.User.email == email))
    return result.scalar_one_or_none()

async def get_user(db: AsyncSession, user_id: uuid.UUID):
    """Obtiene un usuario por su ID."""
    result = await db.execute(
        select(models.User)
        .options(
            selectinload(models.User.roles),
            selectinload(models.User.farms_owned),
            selectinload(models.User.animals_owned),
            selectinload(models.User.farm_accesses),
            selectinload(models.User.accesses_assigned),
            selectinload(models.User.master_data_created),
            selectinload(models.User.health_events_administered),
            selectinload(models.User.feedings_administered),
            selectinload(models.User.config_params_updated),
            selectinload(models.User.transactions_from_owner),
            selectinload(models.User.transactions_to_owner),
            selectinload(models.User.role_permissions_granted),
            selectinload(models.User.grupos_created)
        )
        .filter(models.User.id == user_id)
    )
    return result.scalar_one_or_none()

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Obtiene una lista de usuarios."""
    result = await db.execute(
        select(models.User)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def create_user(db: AsyncSession, user: schemas.UserCreate):
    """Crea un nuevo usuario."""
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        password_hash=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=user.phone_number
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(db: AsyncSession, user_id: uuid.UUID, user_update: schemas.UserUpdate):
    """Actualiza un usuario existente."""
    db_user = await get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))

    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def delete_user(db: AsyncSession, user_id: uuid.UUID):
    """Elimina un usuario por su ID."""
    db_user = await get_user(db, user_id)
    if db_user:
        await db.delete(db_user)
        await db.commit()
        return True
    return False

# Funciones CRUD para Role
async def create_role(db: AsyncSession, role: schemas.RoleCreate):
    """Crea un nuevo rol."""
    db_role = models.Role(**role.model_dump())
    db.add(db_role)
    await db.commit()
    await db.refresh(db_role)
    return db_role

async def get_role(db: AsyncSession, role_id: uuid.UUID):
    """Obtiene un rol por su ID."""
    result = await db.execute(select(models.Role).filter(models.Role.id == role_id))
    return result.scalar_one_or_none()

async def get_roles(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Obtiene una lista de roles."""
    result = await db.execute(select(models.Role).offset(skip).limit(limit))
    return result.scalars().all()

async def update_role(db: AsyncSession, role_id: uuid.UUID, role_update: schemas.RoleUpdate):
    """Actualiza un rol existente."""
    db_role = await get_role(db, role_id)
    if not db_role:
        return None
    
    update_data = role_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_role, key, value)
    
    await db.commit()
    await db.refresh(db_role)
    return db_role

async def delete_role(db: AsyncSession, role_id: uuid.UUID):
    """Elimina un rol por su ID."""
    db_role = await get_role(db, role_id)
    if db_role:
        await db.delete(db_role)
        await db.commit()
        return True
    return False

# Funciones CRUD para Permission
async def create_permission(db: AsyncSession, permission: schemas.PermissionCreate):
    """Crea un nuevo permiso."""
    db_permission = models.Permission(**permission.model_dump())
    db.add(db_permission)
    await db.commit()
    await db.refresh(db_permission)
    return db_permission

async def get_permission(db: AsyncSession, permission_id: uuid.UUID):
    """Obtiene un permiso por su ID."""
    result = await db.execute(select(models.Permission).filter(models.Permission.id == permission_id))
    return result.scalar_one_or_none()

async def get_permissions(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Obtiene una lista de permisos."""
    result = await db.execute(select(models.Permission).offset(skip).limit(limit))
    return result.scalars().all()

async def update_permission(db: AsyncSession, permission_id: uuid.UUID, permission_update: schemas.PermissionUpdate):
    """Actualiza un permiso existente."""
    db_permission = await get_permission(db, permission_id)
    if not db_permission:
        return None
    
    update_data = permission_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_permission, key, value)
    
    await db.commit()
    await db.refresh(db_permission)
    return db_permission

async def delete_permission(db: AsyncSession, permission_id: uuid.UUID):
    """Elimina un permiso por su ID."""
    db_permission = await get_permission(db, permission_id)
    if db_permission:
        await db.delete(db_permission)
        await db.commit()
        return True
    return False

# Funciones CRUD para Farm
async def create_farm(db: AsyncSession, farm: schemas.FarmCreate, owner_user_id: uuid.UUID):
    """Crea una nueva finca."""
    db_farm = models.Farm(**farm.model_dump(), owner_user_id=owner_user_id)
    db.add(db_farm)
    await db.commit()
    await db.refresh(db_farm)
    return db_farm

async def get_farm(db: AsyncSession, farm_id: uuid.UUID):
    """Obtiene una finca por su ID."""
    result = await db.execute(
        select(models.Farm)
        .options(selectinload(models.Farm.owner_user))
        .filter(models.Farm.id == farm_id)
    )
    return result.scalar_one_or_none()

async def get_farms(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Obtiene una lista de fincas."""
    result = await db.execute(
        select(models.Farm)
        .options(selectinload(models.Farm.owner_user))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_farms_by_owner_id(db: AsyncSession, owner_user_id: uuid.UUID, skip: int = 0, limit: int = 100):
    """Obtiene una lista de fincas por el ID del usuario propietario."""
    result = await db.execute(
        select(models.Farm)
        .options(selectinload(models.Farm.owner_user))
        .filter(models.Farm.owner_user_id == owner_user_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_farm(db: AsyncSession, farm_id: uuid.UUID, farm_update: schemas.FarmUpdate):
    """Actualiza una finca existente."""
    db_farm = await get_farm(db, farm_id) 
    if not db_farm:
        return None
    
    update_data = farm_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_farm, key, value)
    
    await db.commit()
    await db.refresh(db_farm) 
    
    updated_farm_result = await db.execute(
        select(models.Farm)
        .options(selectinload(models.Farm.owner_user)) 
        .filter(models.Farm.id == farm_id)
    )
    updated_farm = updated_farm_result.scalar_one_or_none()
    
    return updated_farm 

async def delete_farm(db: AsyncSession, farm_id: uuid.UUID):
    """Elimina una finca por su ID."""
    db_farm = await get_farm(db, farm_id)
    if db_farm:
        await db.delete(db_farm)
        await db.commit()
        return True
    return False

# Funciones CRUD para Lot
async def create_lot(db: AsyncSession, lot: schemas.LotCreate):
    """
    Crea un nuevo lote en la base de datos.
    El farm_id ya viene incluido en el esquema LotCreate.
    """
    db_lot = models.Lot(**lot.model_dump()) 
    db.add(db_lot)
    await db.commit()
    await db.refresh(db_lot) 

    created_lot_result = await db.execute(
        select(models.Lot)
        .options(
            selectinload(models.Lot.farm).selectinload(models.Farm.owner_user) 
        ) 
        .filter(models.Lot.id == db_lot.id)
    )
    loaded_lot = created_lot_result.scalar_one_or_none()
    return loaded_lot

async def get_lot(db: AsyncSession, lot_id: uuid.UUID):
    """Obtiene un lote por su ID."""
    result = await db.execute(
        select(models.Lot)
        .options(
            selectinload(models.Lot.farm).selectinload(models.Farm.owner_user) # Carga anidada!
        ) 
        .filter(models.Lot.id == lot_id)
    )
    return result.scalar_one_or_none()

async def get_lots(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Obtiene una lista de lotes."""
    result = await db.execute(
        select(models.Lot)
        .options(
            selectinload(models.Lot.farm).selectinload(models.Farm.owner_user) # Carga anidada!
        ) 
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_lots_by_farm_id(db: AsyncSession, farm_id: uuid.UUID, skip: int = 0, limit: int = 100):
    """Obtiene una lista de lotes para una finca específica."""
    result = await db.execute(
        select(models.Lot)
        .options(
            selectinload(models.Lot.farm).selectinload(models.Farm.owner_user) # Carga anidada!
        ) 
        .filter(models.Lot.farm_id == farm_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_lot_by_farm_id_and_name(db: AsyncSession, farm_id: uuid.UUID, name: str):
    """Obtiene un lote por su ID de finca y nombre."""
    result = await db.execute(
        select(models.Lot)
        .filter(models.Lot.farm_id == farm_id, models.Lot.name == name)
    )
    return result.scalar_one_or_none()


async def update_lot(db: AsyncSession, lot_id: uuid.UUID, lot_update: schemas.LotUpdate):
    """Actualiza un lote existente."""
    db_lot = await get_lot(db, lot_id)
    if not db_lot:
        return None
    
    update_data = lot_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_lot, key, value)
    
    await db.commit()
    await db.refresh(db_lot) 
    
    updated_lot_result = await db.execute(
        select(models.Lot)
        .options(selectinload(models.Lot.farm).selectinload(models.Farm.owner_user)) 
        .filter(models.Lot.id == lot_id)
    )
    updated_lot = updated_lot_result.scalar_one_or_none()
    return updated_lot


async def delete_lot(db: AsyncSession, lot_id: uuid.UUID):
    """Elimina un lote por su ID."""
    db_lot = await get_lot(db, lot_id)
    if db_lot:
        await db.delete(db_lot)
        await db.commit()
        return True
    return False

# Funciones CRUD para MasterData
async def create_master_data(db: AsyncSession, master_data: schemas.MasterDataCreate, created_by_user_id: uuid.UUID):
    """Crea un nuevo dato maestro."""
    db_master_data = models.MasterData(**master_data.model_dump(), created_by_user_id=created_by_user_id)
    db.add(db_master_data)
    await db.commit()
    await db.refresh(db_master_data)
    return db_master_data

async def get_master_data(db: AsyncSession, master_data_id: uuid.UUID):
    """Obtiene un dato maestro por su ID."""
    result = await db.execute(
        select(models.MasterData)
        .options(selectinload(models.MasterData.created_by_user))
        .filter(models.MasterData.id == master_data_id)
    )
    return result.scalar_one_or_none()

async def get_master_data_by_category_and_name(db: AsyncSession, category: str, name: str):
    """Obtiene un dato maestro por su categoría y nombre."""
    result = await db.execute(
        select(models.MasterData)
        .filter(models.MasterData.category == category, models.MasterData.name == name)
    )
    return result.scalar_one_or_none()

async def get_master_data_by_category(db: AsyncSession, category: str, skip: int = 0, limit: int = 100):
    """Obtiene una lista de datos maestros por categoría."""
    result = await db.execute(
        select(models.MasterData)
        .options(selectinload(models.MasterData.created_by_user))
        .filter(models.MasterData.category == category)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_all_master_data(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Obtiene todos los datos maestros."""
    result = await db.execute(
        select(models.MasterData)
        .options(selectinload(models.MasterData.created_by_user))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_master_data(db: AsyncSession, master_data_id: uuid.UUID, master_data_update: schemas.MasterDataUpdate):
    """Actualiza un dato maestro existente."""
    db_master_data = await get_master_data(db, master_data_id)
    if not db_master_data:
        return None
    
    update_data = master_data_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_master_data, key, value)
    
    await db.commit()
    await db.refresh(db_master_data)
    return db_master_data

async def delete_master_data(db: AsyncSession, master_data_id: uuid.UUID):
    """Elimina un dato maestro por su ID."""
    db_master_data = await get_master_data(db, master_data_id)
    if db_master_data:
        await db.delete(db_master_data)
        await db.commit()
        return True
    return False

# Funciones CRUD para Animal
async def create_animal(db: AsyncSession, animal: schemas.AnimalCreate, owner_user_id: uuid.UUID):
    """Crea un nuevo animal."""
    db_animal = models.Animal(**animal.model_dump(), owner_user_id=owner_user_id)
    db.add(db_animal)
    await db.commit()
    await db.refresh(db_animal)
    # Volver a cargar el animal con todas sus relaciones para la respuesta
    created_animal_result = await db.execute(
        select(models.Animal)
        .options(
            selectinload(models.Animal.owner_user),
            selectinload(models.Animal.species),
            selectinload(models.Animal.breed),
            selectinload(models.Animal.current_lot).selectinload(models.Lot.farm), # Carga anidada para lot.farm
            selectinload(models.Animal.mother),
            selectinload(models.Animal.father),
            # Incluir otras relaciones necesarias para schemas.Animal si no se cargan automáticamente
            # selectinload(models.Animal.groups_history),
            # selectinload(models.Animal.locations_history),
            # etc.
        )
        .filter(models.Animal.id == db_animal.id)
    )
    loaded_animal = created_animal_result.scalar_one_or_none()
    return loaded_animal


async def get_animal(db: AsyncSession, animal_id: uuid.UUID):
    """Obtiene un animal por su ID."""
    result = await db.execute(
        select(models.Animal)
        .options(
            selectinload(models.Animal.owner_user),
            selectinload(models.Animal.species),
            selectinload(models.Animal.breed),
            selectinload(models.Animal.current_lot).selectinload(models.Lot.farm), # Carga anidada
            selectinload(models.Animal.mother),
            selectinload(models.Animal.father),
            selectinload(models.Animal.groups_history),
            selectinload(models.Animal.locations_history),
            selectinload(models.Animal.health_events_pivot), # Asegúrate de que esto cargue bien
            selectinload(models.Animal.reproductive_events),
            selectinload(models.Animal.sire_reproductive_events),
            selectinload(models.Animal.weighings),
            selectinload(models.Animal.feedings_pivot),
            selectinload(models.Animal.transactions),
            selectinload(models.Animal.offspring_born_events),
        )
        .filter(models.Animal.id == animal_id)
    )
    return result.scalar_one_or_none()

async def get_animals(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Obtiene una lista de animales (general, sin filtros de usuario/finca)."""
    result = await db.execute(
        select(models.Animal)
        .options(
            selectinload(models.Animal.owner_user),
            selectinload(models.Animal.species),
            selectinload(models.Animal.breed),
            selectinload(models.Animal.current_lot).selectinload(models.Lot.farm), # Carga anidada
            selectinload(models.Animal.mother),
            selectinload(models.Animal.father),
        )
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_animals_by_user_and_filters(
    db: AsyncSession, 
    user_id: uuid.UUID, 
    farm_id: Optional[uuid.UUID] = None, 
    lot_id: Optional[uuid.UUID] = None,
    accessible_farm_ids: Optional[List[uuid.UUID]] = None, # IDs de fincas a las que el usuario tiene acceso
    skip: int = 0, 
    limit: int = 100
):
    """
    Obtiene una lista de animales propiedad del usuario o de fincas a las que tiene acceso,
    opcionalmente filtrada por farm_id y/o lot_id.
    """
    query = select(models.Animal).options(
        selectinload(models.Animal.owner_user),
        selectinload(models.Animal.species),
        selectinload(models.Animal.breed),
        selectinload(models.Animal.current_lot).selectinload(models.Lot.farm) # Carga anidada para lot.farm
    )

    # Filtrar por animales propiedad del usuario o animales en fincas accesibles
    # La lógica `or_` permite que el animal sea propiedad del usuario O que esté en una de sus fincas accesibles
    auth_filter = or_(
        models.Animal.owner_user_id == user_id,
        models.Animal.current_lot.has(models.Lot.farm_id.in_(accessible_farm_ids))
    )
    query = query.filter(auth_filter)

    if farm_id:
        # Asegurarse de que el farm_id solicitado esté en la lista de fincas accesibles
        if accessible_farm_ids and farm_id not in accessible_farm_ids:
            # Esto ya debería ser manejado por el router, pero es una doble capa de seguridad
            pass 
        query = query.filter(models.Animal.current_lot.has(models.Lot.farm_id == farm_id))

    if lot_id:
        query = query.filter(models.Animal.current_lot_id == lot_id)

    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

async def update_animal(db: AsyncSession, animal_id: uuid.UUID, animal_update: schemas.AnimalUpdate):
    """Actualiza un animal existente."""
    db_animal = await get_animal(db, animal_id)
    if not db_animal:
        return None
    
    update_data = animal_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_animal, key, value)
    
    await db.commit()
    await db.refresh(db_animal)
    # Re-cargar el animal con todas sus relaciones para la respuesta
    updated_animal_result = await db.execute(
        select(models.Animal)
        .options(
            selectinload(models.Animal.owner_user),
            selectinload(models.Animal.species),
            selectinload(models.Animal.breed),
            selectinload(models.Animal.current_lot).selectinload(models.Lot.farm), # Carga anidada para lot.farm
            selectinload(models.Animal.mother),
            selectinload(models.Animal.father),
            # Incluir otras relaciones necesarias para schemas.Animal si no se cargan automáticamente
        )
        .filter(models.Animal.id == animal_id)
    )
    loaded_animal = updated_animal_result.scalar_one_or_none()
    return loaded_animal

async def delete_animal(db: AsyncSession, animal_id: uuid.UUID):
    """Elimina un animal por su ID."""
    db_animal = await get_animal(db, animal_id)
    if db_animal:
        await db.delete(db_animal)
        await db.commit()
        return True
    return False

# Funciones CRUD para Grupo
async def create_grupo(db: AsyncSession, grupo: schemas.GrupoCreate, created_by_user_id: uuid.UUID):
    """Crea un nuevo grupo."""
    db_grupo = models.Grupo(**grupo.model_dump(), created_by_user_id=created_by_user_id)
    db.add(db_grupo)
    await db.commit()
    await db.refresh(db_grupo)
    # Re-cargar el grupo con sus relaciones para la respuesta
    created_grupo_result = await db.execute(
        select(models.Grupo)
        .options(
            selectinload(models.Grupo.purpose),
            selectinload(models.Grupo.created_by_user)
        )
        .filter(models.Grupo.id == db_grupo.id)
    )
    loaded_grupo = created_grupo_result.scalar_one_or_none()
    return loaded_grupo

async def get_grupo(db: AsyncSession, grupo_id: uuid.UUID):
    """Obtiene un grupo por su ID."""
    result = await db.execute(
        select(models.Grupo)
        .options(
            selectinload(models.Grupo.purpose),
            selectinload(models.Grupo.created_by_user)
        )
        .filter(models.Grupo.id == grupo_id)
    )
    return result.scalar_one_or_none()

async def get_grupos(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Obtiene una lista de todos los grupos (sin filtro por creador)."""
    result = await db.execute(
        select(models.Grupo)
        .options(
            selectinload(models.Grupo.purpose),
            selectinload(models.Grupo.created_by_user)
        )
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

# NUEVA FUNCIÓN: Obtener grupos por el ID del usuario que los creó
async def get_grupos_by_created_by_user_id(db: AsyncSession, created_by_user_id: uuid.UUID, skip: int = 0, limit: int = 100):
    """Obtiene una lista de grupos creados por un usuario específico."""
    result = await db.execute(
        select(models.Grupo)
        .options(
            selectinload(models.Grupo.purpose),
            selectinload(models.Grupo.created_by_user)
        )
        .filter(models.Grupo.created_by_user_id == created_by_user_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def update_grupo(db: AsyncSession, grupo_id: uuid.UUID, grupo_update: schemas.GrupoUpdate):
    """Actualiza un grupo existente."""
    db_grupo = await get_grupo(db, grupo_id)
    if not db_grupo:
        return None
    
    update_data = grupo_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_grupo, key, value)
    
    await db.commit()
    await db.refresh(db_grupo)
    # Re-cargar el grupo con sus relaciones para la respuesta
    updated_grupo_result = await db.execute(
        select(models.Grupo)
        .options(
            selectinload(models.Grupo.purpose),
            selectinload(models.Grupo.created_by_user)
        )
        .filter(models.Grupo.id == grupo_id)
    )
    loaded_grupo = updated_grupo_result.scalar_one_or_none()
    return loaded_grupo

async def delete_grupo(db: AsyncSession, grupo_id: uuid.UUID):
    """Elimina un grupo por su ID."""
    db_grupo = await get_grupo(db, grupo_id)
    if db_grupo:
        await db.delete(db_grupo)
        await db.commit()
        return True
    return False

# Funciones CRUD para AnimalGroup
async def create_animal_group(db: AsyncSession, animal_group: schemas.AnimalGroupCreate):
    """Asocia un animal a un grupo."""
    db_animal_group = models.AnimalGroup(**animal_group.model_dump())
    db.add(db_animal_group)
    await db.commit()
    await db.refresh(db_animal_group)
    # Re-cargar el animal_group con sus relaciones para la respuesta
    created_animal_group_result = await db.execute(
        select(models.AnimalGroup)
        .options(
            selectinload(models.AnimalGroup.animal),
            selectinload(models.AnimalGroup.grupo)
        )
        .filter(models.AnimalGroup.animal_id == db_animal_group.animal_id, 
                models.AnimalGroup.grupo_id == db_animal_group.grupo_id)
    )
    loaded_animal_group = created_animal_group_result.scalar_one_or_none()
    return loaded_animal_group


async def get_animal_group(db: AsyncSession, animal_id: uuid.UUID, grupo_id: uuid.UUID):
    """Obtiene una asociación animal-grupo específica."""
    result = await db.execute(
        select(models.AnimalGroup)
        .options(
            selectinload(models.AnimalGroup.animal),
            selectinload(models.AnimalGroup.grupo)
        )
        .filter(models.AnimalGroup.animal_id == animal_id, models.AnimalGroup.grupo_id == grupo_id)
    )
    return result.scalar_one_or_none()

async def get_animal_groups_by_animal(db: AsyncSession, animal_id: uuid.UUID, skip: int = 0, limit: int = 100):
    """Obtiene todas las asociaciones de grupo para un animal específico."""
    result = await db.execute(
        select(models.AnimalGroup)
        .options(
            selectinload(models.AnimalGroup.animal),
            selectinload(models.AnimalGroup.grupo)
        )
        .filter(models.AnimalGroup.animal_id == animal_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_animal_groups_by_grupo(db: AsyncSession, grupo_id: uuid.UUID, skip: int = 0, limit: int = 100):
    """Obtiene todas las asociaciones de animales para un grupo específico."""
    result = await db.execute(
        select(models.AnimalGroup)
        .options(
            selectinload(models.AnimalGroup.animal),
            selectinload(models.AnimalGroup.grupo)
        )
        .filter(models.AnimalGroup.grupo_id == grupo_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

# NUEVA FUNCIÓN: Obtener asociaciones animal-grupo con filtros y autorización
async def get_animal_groups_with_filters(
    db: AsyncSession,
    animal_id: Optional[uuid.UUID] = None,
    grupo_id: Optional[uuid.UUID] = None,
    user_id: uuid.UUID = None, # El usuario actual
    accessible_farm_ids: Optional[List[uuid.UUID]] = None, # Fincas a las que el usuario tiene acceso
    user_created_grupo_ids: Optional[List[uuid.UUID]] = None, # Grupos creados por el usuario
    skip: int = 0,
    limit: int = 100
):
    """
    Obtiene asociaciones animal-grupo filtradas por animal_id, grupo_id y acceso del usuario.
    El usuario debe tener acceso al animal (ser propietario o tener acceso a la finca del animal)
    O debe haber creado el grupo.
    """
    query = select(models.AnimalGroup).options(
        selectinload(models.AnimalGroup.animal).selectinload(models.Animal.current_lot).selectinload(models.Lot.farm),
        selectinload(models.AnimalGroup.grupo).selectinload(models.Grupo.created_by_user)
    )

    # Construir filtros basados en los parámetros de entrada
    filters = []
    if animal_id:
        filters.append(models.AnimalGroup.animal_id == animal_id)
    if grupo_id:
        filters.append(models.AnimalGroup.grupo_id == grupo_id)
    
    # Aplicar la lógica de autorización:
    # El usuario debe ser el propietario del animal, O tener acceso a la finca del animal,
    # O haber creado el grupo.
    
    auth_filters = []
    
    # Condición 1: Animal es propiedad del usuario
    auth_filters.append(models.AnimalGroup.animal.has(models.Animal.owner_user_id == user_id))

    # Condición 2: Animal está en una finca a la que el usuario tiene acceso
    if accessible_farm_ids:
        auth_filters.append(models.AnimalGroup.animal.has(
            models.Animal.current_lot.has(models.Lot.farm_id.in_(accessible_farm_ids))
        ))

    # Condición 3: Grupo fue creado por el usuario
    if user_created_grupo_ids:
        auth_filters.append(models.AnimalGroup.grupo_id.in_(user_created_grupo_ids))
    
    # Combinar los filtros de autorización con OR
    if auth_filters:
        query = query.filter(or_(*auth_filters))

    # Aplicar los filtros de consulta (animal_id, grupo_id)
    if filters:
        query = query.filter(*filters)


    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

async def update_animal_group(db: AsyncSession, animal_id: uuid.UUID, grupo_id: uuid.UUID, animal_group_update: schemas.AnimalGroupUpdate):
    """Actualiza una asociación animal-grupo existente."""
    db_animal_group = await get_animal_group(db, animal_id, grupo_id)
    if not db_animal_group:
        return None
    
    update_data = animal_group_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_animal_group, key, value)
    
    await db.commit()
    await db.refresh(db_animal_group)
    # Re-cargar el animal_group con sus relaciones para la respuesta
    updated_animal_group_result = await db.execute(
        select(models.AnimalGroup)
        .options(
            selectinload(models.AnimalGroup.animal),
            selectinload(models.AnimalGroup.grupo)
        )
        .filter(models.AnimalGroup.animal_id == animal_id, models.AnimalGroup.grupo_id == grupo_id)
    )
    loaded_animal_group = updated_animal_group_result.scalar_one_or_none()
    return loaded_animal_group


async def delete_animal_group(db: AsyncSession, animal_id: uuid.UUID, grupo_id: uuid.UUID):
    """Elimina una asociación animal-grupo."""
    db_animal_group = await get_animal_group(db, animal_id, grupo_id)
    if db_animal_group:
        await db.delete(db_animal_group)
        await db.commit()
        return True
    return False

# Funciones CRUD para HealthEvent
async def create_health_event(
    db: AsyncSession,
    health_event: schemas.HealthEventCreate,
    administered_by_user_id: uuid.UUID,
    animal_ids: List[uuid.UUID] # Recibe los IDs de los animales
):
    """Crea un nuevo evento de salud y asocia los animales."""
    health_event_data = health_event.model_dump(exclude={"animal_ids"})
    db_health_event = models.HealthEvent(
        **health_event_data,
        administered_by_user_id=administered_by_user_id
    )
    db.add(db_health_event)
    await db.flush() # Flush para obtener el ID del evento antes de las asociaciones

    # Crear asociaciones en la tabla pivote AnimalHealthEventPivot
    for animal_id in animal_ids:
        db_pivot = models.AnimalHealthEventPivot(
            health_event_id=db_health_event.id,
            animal_id=animal_id,
            # Eliminado: created_at=datetime.now()
        )
        db.add(db_pivot)

    await db.commit()
    await db.refresh(db_health_event)

    # Cargar las relaciones para la respuesta
    result = await db.execute(
        select(models.HealthEvent)
        .options(
            selectinload(models.HealthEvent.product),
            selectinload(models.HealthEvent.administered_by_user),
            selectinload(models.HealthEvent.animals_affected)
            .selectinload(models.AnimalHealthEventPivot.animal)
            .selectinload(models.Animal.current_lot).selectinload(models.Lot.farm), # Asegura que la finca del animal esté cargada
            selectinload(models.HealthEvent.animals_affected)
            .selectinload(models.AnimalHealthEventPivot.health_event) # ¡Cargar el evento de salud padre también!
        )
        .filter(models.HealthEvent.id == db_health_event.id)
    )
    return result.scalar_one_or_none()

async def get_health_event(db: AsyncSession, health_event_id: uuid.UUID):
    """Obtiene un evento de salud por su ID."""
    result = await db.execute(
        select(models.HealthEvent)
        .options(
            selectinload(models.HealthEvent.product),
            selectinload(models.HealthEvent.administered_by_user),
            selectinload(models.HealthEvent.animals_affected)
            .selectinload(models.AnimalHealthEventPivot.animal)
            .selectinload(models.Animal.current_lot).selectinload(models.Lot.farm), # Asegura que la finca del animal esté cargada
            selectinload(models.HealthEvent.animals_affected)
            .selectinload(models.AnimalHealthEventPivot.health_event) # ¡Cargar el evento de salud padre también!
        )
        .filter(models.HealthEvent.id == health_event_id)
    )
    return result.scalar_one_or_none()

async def get_health_events_with_filters(
    db: AsyncSession,
    user_id: uuid.UUID,
    accessible_farm_ids: List[uuid.UUID],
    animal_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Obtiene eventos de salud filtrados por acceso del usuario o por animal_id.
    Un evento es accesible si el usuario lo administró o tiene acceso a al menos uno de los animales afectados.
    """
    query = select(models.HealthEvent).options(
        selectinload(models.HealthEvent.product),
        selectinload(models.HealthEvent.administered_by_user),
        selectinload(models.HealthEvent.animals_affected)
        .selectinload(models.AnimalHealthEventPivot.animal)
        .selectinload(models.Animal.current_lot).selectinload(models.Lot.farm), # Para cargar la finca del animal
        selectinload(models.HealthEvent.animals_affected)
        .selectinload(models.AnimalHealthEventPivot.health_event) # ¡Cargar el evento de salud padre también!
    )

    # Lógica de autorización
    auth_conditions = [
        models.HealthEvent.administered_by_user_id == user_id # Usuario es el administrador
    ]

    # Usuario tiene acceso a alguna de las fincas donde están los animales afectados
    if accessible_farm_ids:
        # Busca eventos donde CUALQUIERA de los animales afectados por el evento está en una finca accesible
        auth_conditions.append(
            models.HealthEvent.animals_affected.any(
                models.AnimalHealthEventPivot.animal.has(
                    models.Animal.current_lot.has(
                        models.Lot.farm_id.in_(accessible_farm_ids)
                    )
                )
            )
        )
    
    query = query.filter(or_(*auth_conditions))

    # Filtro adicional por animal_id si se proporciona
    if animal_id:
        query = query.filter(
            models.HealthEvent.animals_affected.any(
                models.AnimalHealthEventPivot.animal_id == animal_id
            )
        )

    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()


async def update_health_event(db: AsyncSession, health_event_id: uuid.UUID, health_event_update: schemas.HealthEventUpdate):
    """Actualiza un evento de salud existente."""
    db_health_event = await get_health_event(db, health_event_id)
    if not db_health_event:
        return None
    
    update_data = health_event_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_health_event, key, value)
    
    await db.commit()
    await db.refresh(db_health_event)

    # Recargar con relaciones para la respuesta
    updated_event_result = await db.execute(
        select(models.HealthEvent)
        .options(
            selectinload(models.HealthEvent.product),
            selectinload(models.HealthEvent.administered_by_user),
            selectinload(models.HealthEvent.animals_affected)
            .selectinload(models.AnimalHealthEventPivot.animal)
            .selectinload(models.Animal.current_lot).selectinload(models.Lot.farm),
            selectinload(models.HealthEvent.animals_affected)
            .selectinload(models.AnimalHealthEventPivot.health_event) # ¡Cargar el evento de salud padre también!
        )
        .filter(models.HealthEvent.id == health_event_id)
    )
    return updated_event_result.scalar_one_or_none()


async def delete_health_event(db: AsyncSession, health_event_id: uuid.UUID):
    """Elimina un evento de salud por su ID, incluyendo sus asociaciones."""
    db_health_event = await get_health_event(db, health_event_id)
    if db_health_event:
        # Eliminar las asociaciones en la tabla pivote primero
        await db.execute(
            delete(models.AnimalHealthEventPivot).where(models.AnimalHealthEventPivot.health_event_id == health_event_id)
        )
        await db.delete(db_health_event)
        await db.commit()
        return True
    return False

# Para `routers/health_events.py` que necesita acceder a `AnimalHealthEventPivot` para validar
async def get_animal_health_pivot(db: AsyncSession, health_event_id: uuid.UUID, animal_id: uuid.UUID):
    """Obtiene una asociación Animal-HealthEvent específica."""
    result = await db.execute(
        select(models.AnimalHealthEventPivot)
        .filter(models.AnimalHealthEventPivot.health_event_id == health_event_id,
                models.AnimalHealthEventPivot.animal_id == animal_id)
    )
    return result.scalar_one_or_none()

# Funciones CRUD para ReproductiveEvent
async def create_reproductive_event(db: AsyncSession, event: schemas.ReproductiveEventCreate):
    """Crea un nuevo evento reproductivo."""
    db_event = models.ReproductiveEvent(**event.model_dump())
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)
    # Re-cargar el evento reproductivo con sus relaciones para la respuesta
    created_reproductive_event_result = await db.execute(
        select(models.ReproductiveEvent)
        .options(
            selectinload(models.ReproductiveEvent.animal),
            selectinload(models.ReproductiveEvent.sire_animal),
            selectinload(models.ReproductiveEvent.offspring).selectinload(models.OffspringBorn.offspring_animal)
        )
        .filter(models.ReproductiveEvent.id == db_event.id)
    )
    loaded_event = created_reproductive_event_result.scalar_one_or_none()
    return loaded_event

async def get_reproductive_event(db: AsyncSession, event_id: uuid.UUID):
    """Obtiene un evento reproductivo por su ID."""
    result = await db.execute(
        select(models.ReproductiveEvent)
        .options(
            selectinload(models.ReproductiveEvent.animal),
            selectinload(models.ReproductiveEvent.sire_animal),
            selectinload(models.ReproductiveEvent.offspring).selectinload(models.OffspringBorn.offspring_animal)
        )
        .filter(models.ReproductiveEvent.id == event_id)
    )
    return result.scalar_one_or_none()

async def get_reproductive_events(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Obtiene una lista de eventos reproductivos."""
    result = await db.execute(
        select(models.ReproductiveEvent)
        .options(
            selectinload(models.ReproductiveEvent.animal),
            selectinload(models.ReproductiveEvent.sire_animal)
        )
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_reproductive_event(db: AsyncSession, event_id: uuid.UUID, event_update: schemas.ReproductiveEventUpdate):
    """Actualiza un evento reproductivo existente."""
    db_event = await get_reproductive_event(db, event_id)
    if not db_event:
        return None
    
    update_data = event_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_event, key, value)
    
    await db.commit()
    await db.refresh(db_event)
    # Re-cargar el evento reproductivo con sus relaciones para la respuesta
    updated_reproductive_event_result = await db.execute(
        select(models.ReproductiveEvent)
        .options(
            selectinload(models.ReproductiveEvent.animal),
            selectinload(models.ReproductiveEvent.sire_animal),
            selectinload(models.ReproductiveEvent.offspring).selectinload(models.OffspringBorn.offspring_animal)
        )
        .filter(models.ReproductiveEvent.id == event_id)
    )
    loaded_event = updated_reproductive_event_result.scalar_one_or_none()
    return loaded_event

async def delete_reproductive_event(db: AsyncSession, event_id: uuid.UUID):
    """Elimina un evento reproductivo por su ID."""
    db_event = await get_reproductive_event(db, event_id)
    if db_event:
        await db.delete(db_event)
        await db.commit()
        return True
    return False

# Funciones CRUD para OffspringBorn
async def create_offspring_born(db: AsyncSession, offspring: schemas.OffspringBornCreate):
    """Registra una cría nacida de un evento reproductivo."""
    db_offspring = models.OffspringBorn(**offspring.model_dump())
    db.add(db_offspring)
    await db.commit()
    await db.refresh(db_offspring)
    # Re-cargar la cría nacida con sus relaciones para la respuesta
    created_offspring_result = await db.execute(
        select(models.OffspringBorn)
        .options(
            selectinload(models.OffspringBorn.reproductive_event),
            selectinload(models.OffspringBorn.offspring_animal)
        )
        .filter(models.OffspringBorn.id == db_offspring.id)
    )
    loaded_offspring = created_offspring_result.scalar_one_or_none()
    return loaded_offspring

async def get_offspring_born(db: AsyncSession, offspring_id: uuid.UUID):
    """Obtiene un registro de cría nacida por su ID."""
    result = await db.execute(
        select(models.OffspringBorn)
        .options(
            selectinload(models.OffspringBorn.reproductive_event),
            selectinload(models.OffspringBorn.offspring_animal)
        )
        .filter(models.OffspringBorn.id == offspring_id)
    )
    return result.scalar_one_or_none()

async def get_offspring_born_by_event(db: AsyncSession, reproductive_event_id: uuid.UUID, skip: int = 0, limit: int = 100):
    """Obtiene las crías nacidas para un evento reproductivo específico."""
    result = await db.execute(
        select(models.OffspringBorn)
        .options(
            selectinload(models.OffspringBorn.reproductive_event),
            selectinload(models.OffspringBorn.offspring_animal)
        )
        .filter(models.OffspringBorn.reproductive_event_id == reproductive_event_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_offspring_born(db: AsyncSession, offspring_id: uuid.UUID, offspring_update: schemas.OffspringBornUpdate):
    """Actualiza un registro de cría nacida existente."""
    db_offspring = await get_offspring_born(db, offspring_id)
    if not db_offspring:
        return None
    
    update_data = offspring_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_offspring, key, value)
    
    await db.commit()
    await db.refresh(db_offspring)
    # Re-cargar la cría nacida con sus relaciones para la respuesta
    updated_offspring_result = await db.execute(
        select(models.OffspringBorn)
        .options(
            selectinload(models.OffspringBorn.reproductive_event),
            selectinload(models.OffspringBorn.offspring_animal)
        )
        .filter(models.OffspringBorn.id == offspring_id)
    )
    loaded_offspring = updated_offspring_result.scalar_one_or_none()
    return loaded_offspring

async def delete_offspring_born(db: AsyncSession, offspring_id: uuid.UUID):
    """Elimina un registro de cría nacida."""
    db_offspring = await get_offspring_born(db, offspring_id)
    if db_offspring:
        await db.delete(db_offspring)
        await db.commit()
        return True
    return False

# Funciones CRUD para Weighing
async def create_weighing(db: AsyncSession, weighing: schemas.WeighingCreate):
    """Crea un nuevo registro de pesaje."""
    db_weighing = models.Weighing(**weighing.model_dump())
    db.add(db_weighing)
    await db.commit()
    await db.refresh(db_weighing)
    # Re-cargar el pesaje con sus relaciones para la respuesta
    created_weighing_result = await db.execute(
        select(models.Weighing)
        .options(selectinload(models.Weighing.animal))
        .filter(models.Weighing.id == db_weighing.id)
    )
    loaded_weighing = created_weighing_result.scalar_one_or_none()
    return loaded_weighing


async def get_weighing(db: AsyncSession, weighing_id: uuid.UUID):
    """Obtiene un registro de pesaje por su ID."""
    result = await db.execute(
        select(models.Weighing)
        .options(selectinload(models.Weighing.animal))
        .filter(models.Weighing.id == weighing_id)
    )
    return result.scalar_one_or_none()

async def get_weighings_by_animal(db: AsyncSession, animal_id: uuid.UUID, skip: int = 0, limit: int = 100):
    """Obtiene los registros de pesaje para un animal específico."""
    result = await db.execute(
        select(models.Weighing)
        .options(selectinload(models.Weighing.animal))
        .filter(models.Weighing.animal_id == animal_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_weighing(db: AsyncSession, weighing_id: uuid.UUID, weighing_update: schemas.WeighingUpdate):
    """Actualiza un registro de pesaje existente."""
    db_weighing = await get_weighing(db, weighing_id)
    if not db_weighing:
        return None
    
    update_data = weighing_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_weighing, key, value)
    
    await db.commit()
    await db.refresh(db_weighing)
    # Re-cargar el pesaje con sus relaciones para la respuesta
    updated_weighing_result = await db.execute(
        select(models.Weighing)
        .options(selectinload(models.Weighing.animal))
        .filter(models.Weighing.id == weighing_id)
    )
    loaded_weighing = updated_weighing_result.scalar_one_or_none()
    return loaded_weighing

async def delete_weighing(db: AsyncSession, weighing_id: uuid.UUID):
    """Elimina un registro de pesaje."""
    db_weighing = await get_weighing(db, weighing_id)
    if db_weighing:
        await db.delete(db_weighing)
        await db.commit()
        return True
    return False

# Funciones CRUD para Feeding
async def create_feeding(db: AsyncSession, feeding: schemas.FeedingCreate, administered_by_user_id: uuid.UUID):
    """
    Crea un nuevo registro de alimentación y lo asocia a los animales especificados.
    """
    feeding_data = feeding.model_dump(exclude={"animal_ids"})
    db_feeding = models.Feeding(
        **feeding_data,
        administered_by_user_id=administered_by_user_id
    )
    db.add(db_feeding)
    await db.commit()
    await db.refresh(db_feeding)

    for animal_id in feeding.animal_ids:
        db_pivot = models.AnimalFeedingPivot(
            feeding_id=db_feeding.id,
            animal_id=animal_id
        )
        db.add(db_pivot)
    await db.commit()
    # Re-cargar el feeding con sus relaciones para la respuesta
    created_feeding_result = await db.execute(
        select(models.Feeding)
        .options(
            selectinload(models.Feeding.feed_type),
            selectinload(models.Feeding.supplement),
            selectinload(models.Feeding.administered_by_user),
            selectinload(models.Feeding.animals_fed).selectinload(models.AnimalFeedingPivot.animal)
        )
        .filter(models.Feeding.id == db_feeding.id)
    )
    loaded_feeding = created_feeding_result.scalar_one_or_none()
    return loaded_feeding


async def get_feeding(db: AsyncSession, feeding_id: uuid.UUID):
    """Obtiene un registro de alimentación por su ID."""
    result = await db.execute(
        select(models.Feeding)
        .options(
            selectinload(models.Feeding.feed_type),
            selectinload(models.Feeding.supplement),
            selectinload(models.Feeding.administered_by_user),
            selectinload(models.Feeding.animals_fed).selectinload(models.AnimalFeedingPivot.animal) # Cargar animales afectados
        )
        .filter(models.Feeding.id == feeding_id)
    )
    return result.scalar_one_or_none()

async def get_feedings(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Obtiene una lista de registros de alimentación."""
    result = await db.execute(
        select(models.Feeding)
        .options(
            selectinload(models.Feeding.feed_type),
            selectinload(models.Feeding.supplement),
            selectinload(models.Feeding.administered_by_user)
        )
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_feeding(db: AsyncSession, feeding_id: uuid.UUID, feeding_update: schemas.FeedingUpdate):
    """Actualiza un registro de alimentación existente."""
    db_feeding = await get_feeding(db, feeding_id)
    if not db_feeding:
        return None
    
    update_data = feeding_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_feeding, key, value)
    
    await db.commit()
    await db.refresh(db_feeding)
    # Re-cargar el feeding con sus relaciones para la respuesta
    updated_feeding_result = await db.execute(
        select(models.Feeding)
        .options(
            selectinload(models.Feeding.feed_type),
            selectinload(models.Feeding.supplement),
            selectinload(models.Feeding.administered_by_user),
            selectinload(models.Feeding.animals_fed).selectinload(models.AnimalFeedingPivot.animal)
        )
        .filter(models.Feeding.id == feeding_id)
    )
    loaded_feeding = updated_feeding_result.scalar_one_or_none()
    return loaded_feeding

async def delete_feeding(db: AsyncSession, feeding_id: uuid.UUID):
    """Elimina un registro de alimentación."""
    db_feeding = await get_feeding(db, feeding_id)
    if db_feeding:
        await db.delete(db_feeding)
        await db.commit()
        return True
    return False

# Funciones CRUD para Transaction
async def create_transaction(db: AsyncSession, transaction: schemas.TransactionCreate):
    """Crea una nueva transacción."""
    db_transaction = models.Transaction(**transaction.model_dump())
    db.add(db_transaction)
    await db.commit()
    await db.refresh(db_transaction)
    # Re-cargar la transacción con sus relaciones para la respuesta
    created_transaction_result = await db.execute(
        select(models.Transaction)
        .options(
            selectinload(models.Transaction.animal),
            selectinload(models.Transaction.from_farm),
            selectinload(models.Transaction.to_farm),
            selectinload(models.Transaction.from_owner_user),
            selectinload(models.Transaction.to_owner_user)
        )
        .filter(models.Transaction.id == db_transaction.id)
    )
    loaded_transaction = created_transaction_result.scalar_one_or_none()
    return loaded_transaction

async def get_transaction(db: AsyncSession, transaction_id: uuid.UUID):
    """Obtiene una transacción por su ID."""
    result = await db.execute(
        select(models.Transaction)
        .options(
            selectinload(models.Transaction.animal),
            selectinload(models.Transaction.from_farm),
            selectinload(models.Transaction.to_farm),
            selectinload(models.Transaction.from_owner_user),
            selectinload(models.Transaction.to_owner_user)
        )
        .filter(models.Transaction.id == transaction_id)
    )
    return result.scalar_one_or_none()

async def get_transactions(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Obtiene una lista de transacciones."""
    result = await db.execute(
        select(models.Transaction)
        .options(
            selectinload(models.Transaction.animal),
            selectinload(models.Transaction.from_farm),
            selectinload(models.Transaction.to_farm),
            selectinload(models.Transaction.from_owner_user),
            selectinload(models.Transaction.to_owner_user)
        )
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_transaction(db: AsyncSession, transaction_id: uuid.UUID, transaction_update: schemas.TransactionUpdate):
    """Actualiza una transacción existente."""
    db_transaction = await get_transaction(db, transaction_id)
    if not db_transaction:
        return None
    
    update_data = transaction_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_transaction, key, value)
    
    await db.commit()
    await db.refresh(db_transaction)
    # Re-cargar la transacción con sus relaciones para la respuesta
    updated_transaction_result = await db.execute(
        select(models.Transaction)
        .options(
            selectinload(models.Transaction.animal),
            selectinload(models.Transaction.from_farm),
            selectinload(models.Transaction.to_farm),
            selectinload(models.Transaction.from_owner_user),
            selectinload(models.Transaction.to_owner_user)
        )
        .filter(models.Transaction.id == transaction_id)
    )
    loaded_transaction = updated_transaction_result.scalar_one_or_none()
    return loaded_transaction

async def delete_transaction(db: AsyncSession, transaction_id: uuid.UUID):
    """Elimina una transacción."""
    db_transaction = await get_transaction(db, transaction_id)
    if db_transaction:
        await db.delete(db_transaction)
        await db.commit()
        return True
    return False

# Funciones CRUD para ConfigurationParameter
async def create_configuration_parameter(db: AsyncSession, config_param: schemas.ConfigurationParameterCreate, last_updated_by_user_id: uuid.UUID):
    """Crea un nuevo parámetro de configuración."""
    db_config_param = models.ConfigurationParameter(**config_param.model_dump(), last_updated_by_user_id=last_updated_by_user_id)
    db.add(db_config_param)
    await db.commit()
    await db.refresh(db_config_param)
    # Re-cargar el parámetro de configuración con sus relaciones para la respuesta
    created_config_param_result = await db.execute(
        select(models.ConfigurationParameter)
        .options(selectinload(models.ConfigurationParameter.last_updated_by_user))
        .filter(models.ConfigurationParameter.id == db_config_param.id)
    )
    loaded_config_param = created_config_param_result.scalar_one_or_none()
    return loaded_config_param


async def get_configuration_parameter(db: AsyncSession, config_param_id: uuid.UUID):
    """Obtiene un parámetro de configuración por su ID."""
    result = await db.execute(
        select(models.ConfigurationParameter)
        .options(selectinload(models.ConfigurationParameter.last_updated_by_user))
        .filter(models.ConfigurationParameter.id == config_param_id)
    )
    return result.scalar_one_or_none()

async def get_configuration_parameter_by_name(db: AsyncSession, parameter_name: str):
    """Obtiene un parámetro de configuración por su nombre."""
    result = await db.execute(
        select(models.ConfigurationParameter)
        .options(selectinload(models.ConfigurationParameter.last_updated_by_user))
        .filter(models.ConfigurationParameter.parameter_name == parameter_name)
    )
    return result.scalar_one_or_none()

async def get_all_configuration_parameters(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Obtiene una lista de todos los parámetros de configuración."""
    result = await db.execute(
        select(models.ConfigurationParameter)
        .options(selectinload(models.ConfigurationParameter.last_updated_by_user))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_configuration_parameter(db: AsyncSession, config_param_id: uuid.UUID, config_param_update: schemas.ConfigurationParameterUpdate, last_updated_by_user_id: uuid.UUID):
    """Actualiza un parámetro de configuración existente."""
    db_config_param = await get_configuration_parameter(db, config_param_id)
    if not db_config_param:
        return None
    
    update_data = config_param_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_config_param, key, value)
    
    # Asegurarse de que el usuario que actualizó se registre
    db_config_param.last_updated_by_user_id = last_updated_by_user_id
    db_config_param.updated_at = datetime.now() # Actualiza el timestamp

    await db.commit()
    await db.refresh(db_config_param)
    # Re-cargar el parámetro de configuración con sus relaciones para la respuesta
    updated_config_param_result = await db.execute(
        select(models.ConfigurationParameter)
        .options(selectinload(models.ConfigurationParameter.last_updated_by_user))
        .filter(models.ConfigurationParameter.id == config_param_id)
    )
    loaded_config_param = updated_config_param_result.scalar_one_or_none()
    return loaded_config_param

async def delete_configuration_parameter(db: AsyncSession, config_param_id: uuid.UUID):
    """Elimina un parámetro de configuración."""
    db_config_param = await get_configuration_parameter(db, config_param_id)
    if db_config_param:
        await db.delete(db_config_param)
        await db.commit()
        return True
    return False

# Funciones CRUD para AnimalLocationHistory
async def create_animal_location_history(db: AsyncSession, location_history: schemas.AnimalLocationHistory): 
    """Crea un nuevo registro de historial de ubicación para un animal."""
    db_location = models.AnimalLocationHistory(**location_history.model_dump())
    db.add(db_location)
    await db.commit()
    await db.refresh(db_location)
    # Re-cargar el historial de ubicación con sus relaciones para la respuesta
    created_location_result = await db.execute(
        select(models.AnimalLocationHistory)
        .options(
            selectinload(models.AnimalLocationHistory.animal),
            selectinload(models.AnimalLocationHistory.farm)
        )
        .filter(models.AnimalLocationHistory.id == db_location.id)
    )
    loaded_location = created_location_result.scalar_one_or_none()
    return loaded_location


async def get_animal_location_history(db: AsyncSession, location_history_id: uuid.UUID):
    """Obtiene un registro de historial de ubicación por su ID."""
    result = await db.execute(
        select(models.AnimalLocationHistory)
        .options(
            selectinload(models.AnimalLocationHistory.animal),
            selectinload(models.AnimalLocationHistory.farm)
        )
        .filter(models.AnimalLocationHistory.id == location_history_id)
    )
    return result.scalar_one_or_none()

async def get_animal_location_history_by_animal(db: AsyncSession, animal_id: uuid.UUID, skip: int = 0, limit: int = 100):
    """Obtiene el historial de ubicación para un animal específico."""
    result = await db.execute(
        select(models.AnimalLocationHistory)
        .options(
            selectinload(models.AnimalLocationHistory.animal),
            selectinload(models.AnimalLocationHistory.farm)
        )
        .filter(models.AnimalLocationHistory.animal_id == animal_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_animal_location_history(db: AsyncSession, location_history_id: uuid.UUID, location_history_update: schemas.AnimalLocationHistory): 
    """Actualiza un registro de historial de ubicación existente."""
    db_location = await get_animal_location_history(db, location_history_id)
    if not db_location:
        return None
    
    update_data = location_history_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_location, key, value)
    
    await db.commit()
    await db.refresh(db_location)
    # Re-cargar el historial de ubicación con sus relaciones para la respuesta
    updated_location_result = await db.execute(
        select(models.AnimalLocationHistory)
        .options(
            selectinload(models.AnimalLocationHistory.animal),
            selectinload(models.AnimalLocationHistory.farm)
        )
        .filter(models.AnimalLocationHistory.id == location_history_id)
    )
    loaded_location = updated_location_result.scalar_one_or_none()
    return loaded_location

async def delete_animal_location_history(db: AsyncSession, location_history_id: uuid.UUID):
    """Elimina un registro de historial de ubicación."""
    db_location = await get_animal_location_history(db, location_history_id)
    if db_location:
        await db.delete(db_location)
        await db.commit()
        return True
    return False

# Funciones CRUD adicionales para Role (si no las tienes)
async def get_role_by_name(db: AsyncSession, name: str):
    """Obtiene un rol por su nombre."""
    result = await db.execute(select(models.Role).filter(models.Role.name == name))
    return result.scalar_one_or_none()

# Funciones CRUD adicionales para Permission (si no las tienes)
async def get_permission_by_name(db: AsyncSession, name: str):
    """Obtiene un permiso por su nombre."""
    result = await db.execute(select(models.Permission).filter(models.Permission.name == name))
    return result.scalar_one_or_none()

async def get_permissions_by_module(db: AsyncSession, module_id: uuid.UUID, skip: int = 0, limit: int = 100):
    """Obtiene una lista de permisos filtrada por ID de módulo."""
    result = await db.execute(
        select(models.Permission)
        .options(selectinload(models.Permission.module))
        .filter(models.Permission.module_id == module_id)
    )
    return result.scalars().all()

async def get_module(db: AsyncSession, module_id: uuid.UUID):
    """Obtiene un módulo por su ID."""
    result = await db.execute(select(models.Module).filter(models.Module.id == module_id))
    return result.scalar_one_or_none()

# Funciones CRUD adicionales para UserFarmAccess (necesaria para checks de autorización en routers)
async def get_user_farm_accesses_by_user(db: AsyncSession, user_id: uuid.UUID, skip: int = 0, limit: int = 100):
    """Obtiene todas las asociaciones de acceso a fincas para un usuario específico."""
    result = await db.execute(
        select(models.UserFarmAccess)
        .options(
            selectinload(models.UserFarmAccess.user),
            selectinload(models.UserFarmAccess.farm),
            selectinload(models.UserFarmAccess.assigned_by_user)
        )
        .filter(models.UserFarmAccess.user_id == user_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()
