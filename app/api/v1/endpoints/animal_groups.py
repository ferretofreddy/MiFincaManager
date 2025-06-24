# routers/animal_groups.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Optional

# --- Importaciones de módulos centrales ---
from app import crud, schemas, models # Acceso de alto nivel a tus módulos principales

# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI (get_db, get_current_user, etc.)

router = APIRouter(
    prefix="/animal-groups", # Ojo, se usa guion en la URL para diferenciar de 'grupos'
    tags=["Animal Groups"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.AnimalGroup, status_code=status.HTTP_201_CREATED)
async def create_new_animal_group(
    animal_group: schemas.AnimalGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Asocia un animal a un grupo.
    Requiere autenticación.
    Verifica que el animal y el grupo existan y que el usuario tenga acceso a ellos.
    También verifica que la asociación no exista previamente.
    """
    # 1. Verificar que el animal exista y el usuario sea propietario o tenga acceso a su finca
    db_animal = await crud.get_animal(db, animal_id=animal_group.animal_id)
    if not db_animal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Animal not found."
        )
    
    is_animal_owner = db_animal.owner_user_id == current_user.id
    has_animal_farm_access = False
    if not is_animal_owner and db_animal.current_lot:
        if db_animal.current_lot.farm.owner_user_id == current_user.id:
            has_animal_farm_access = True
        else:
            user_farm_accesses = await crud.get_user_farm_accesses_by_user(db, user_id=current_user.id)
            if any(access.farm_id == db_animal.current_lot.farm.id for access in user_farm_accesses):
                has_animal_farm_access = True
    
    if not (is_animal_owner or has_animal_farm_access):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to associate this animal."
        )

    # 2. Verificar que el grupo exista y el usuario sea quien lo creó
    db_grupo = await crud.get_grupo(db, grupo_id=animal_group.grupo_id)
    if not db_grupo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found."
        )
    
    if db_grupo.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to use this group."
        )

    # 3. Verificar si la asociación ya existe
    existing_animal_group = await crud.get_animal_group(db, animal_id=animal_group.animal_id, grupo_id=animal_group.grupo_id)
    if existing_animal_group:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Animal is already associated with this group."
        )

    # 4. Crear la asociación
    db_animal_group = await crud.create_animal_group(db=db, animal_group=animal_group)
    return db_animal_group

@router.get("/", response_model=List[schemas.AnimalGroup])
async def read_animal_groups(
    skip: int = 0,
    limit: int = 100,
    animal_id: Optional[uuid.UUID] = None,
    grupo_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene una lista de asociaciones animal-grupo.
    Permite filtrar por animal_id o grupo_id.
    Solo muestra asociaciones donde el usuario tiene acceso al animal O ha creado el grupo.
    """
    # Lógica de filtrado y autorización combinada.
    # Primero, obtener los animales y grupos a los que el usuario tiene acceso.

    # Obtener IDs de fincas del usuario (propietario)
    user_owned_farms = await crud.get_farms_by_owner_id(db, owner_user_id=current_user.id)
    user_owned_farm_ids = {f.id for f in user_owned_farms}

    # Obtener IDs de fincas a las que el usuario tiene acceso compartido
    user_farm_accesses = await crud.get_user_farm_accesses_by_user(db, user_id=current_user.id)
    user_shared_farm_ids = {a.farm_id for a in user_farm_accesses}

    # Combinar todas las fincas a las que el usuario tiene acceso
    all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

    # Obtener IDs de grupos creados por el usuario
    user_created_grupos = await crud.get_grupos_by_created_by_user_id(db, created_by_user_id=current_user.id)
    user_created_grupo_ids = {g.id for g in user_created_grupos}

    # Filtrar las asociaciones
    animal_groups = await crud.get_animal_groups_with_filters(
        db,
        animal_id=animal_id,
        grupo_id=grupo_id,
        user_id=current_user.id,
        accessible_farm_ids=list(all_accessible_farm_ids),
        user_created_grupo_ids=list(user_created_grupo_ids),
        skip=skip,
        limit=limit
    )
    return animal_groups

@router.get("/{animal_id}/{grupo_id}", response_model=schemas.AnimalGroup)
async def read_single_animal_group(
    animal_id: uuid.UUID,
    grupo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene una asociación animal-grupo específica por ID de animal y ID de grupo.
    El usuario debe tener acceso al animal O haber creado el grupo.
    """
    db_animal_group = await crud.get_animal_group(db, animal_id=animal_id, grupo_id=grupo_id)
    if not db_animal_group:
        raise HTTPException(status_code=404, detail="Animal Group association not found")
    
    # Verificar acceso al animal
    is_animal_owner = db_animal_group.animal.owner_user_id == current_user.id
    has_animal_farm_access = False
    if not is_animal_owner and db_animal_group.animal.current_lot:
        # Asegurarse de que farm esté cargado en db_animal_group.animal.current_lot.farm
        # crud.get_animal debería cargarlo. Si no, ajustar.
        if db_animal_group.animal.current_lot.farm.owner_user_id == current_user.id:
            has_animal_farm_access = True
        else:
            user_farm_accesses = await crud.get_user_farm_accesses_by_user(db, user_id=current_user.id)
            if any(access.farm_id == db_animal_group.animal.current_lot.farm.id for access in user_farm_accesses):
                has_farm_access = True

    # Verificar si el usuario creó el grupo
    is_grupo_creator = db_animal_group.grupo.created_by_user_id == current_user.id

    if not (is_animal_owner or has_animal_farm_access or is_grupo_creator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this animal group association."
        )
    return db_animal_group

@router.put("/{animal_id}/{grupo_id}", response_model=schemas.AnimalGroup)
async def update_existing_animal_group(
    animal_id: uuid.UUID,
    grupo_id: uuid.UUID,
    animal_group_update: schemas.AnimalGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Actualiza una asociación animal-grupo existente.
    El usuario debe tener acceso al animal O haber creado el grupo para actualizarlo.
    """
    db_animal_group = await crud.get_animal_group(db, animal_id=animal_id, grupo_id=grupo_id)
    if not db_animal_group:
        raise HTTPException(status_code=404, detail="Animal Group association not found")

    # Verificar acceso al animal o ser creador del grupo para permitir la actualización
    is_animal_owner = db_animal_group.animal.owner_user_id == current_user.id
    has_animal_farm_access = False
    if not is_animal_owner and db_animal_group.animal.current_lot:
        if db_animal_group.animal.current_lot.farm.owner_user_id == current_user.id:
            has_animal_farm_access = True
        else:
            user_farm_accesses = await crud.get_user_farm_accesses_by_user(db, user_id=current_user.id)
            if any(access.farm_id == db_animal_group.animal.current_lot.farm.id for access in user_farm_accesses):
                has_farm_access = True

    is_grupo_creator = db_animal_group.grupo.created_by_user_id == current_user.id

    if not (is_animal_owner or has_animal_farm_access or is_grupo_creator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this animal group association."
        )
    
    # Si se intenta cambiar animal_id o grupo_id (lo cual no debería ocurrir con un PUT de ID compuesto)
    # se podría añadir lógica aquí, pero el esquema AnimalGroupUpdate no permite cambiar las claves primarias.
    # Solo permite actualizar `assigned_date`, `removed_date`, `notes`.

    updated_animal_group = await crud.update_animal_group(db, animal_id=animal_id, grupo_id=grupo_id, animal_group_update=animal_group_update)
    return updated_animal_group

@router.delete("/{animal_id}/{grupo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_animal_group(
    animal_id: uuid.UUID,
    grupo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Elimina una asociación animal-grupo.
    El usuario debe tener acceso al animal O haber creado el grupo para eliminarlo.
    """
    db_animal_group = await crud.get_animal_group(db, animal_id=animal_id, grupo_id=grupo_id)
    if not db_animal_group:
        raise HTTPException(status_code=404, detail="Animal Group association not found")

    # Verificar acceso al animal o ser creador del grupo para permitir la eliminación
    is_animal_owner = db_animal_group.animal.owner_user_id == current_user.id
    has_animal_farm_access = False
    if not is_animal_owner and db_animal_group.animal.current_lot:
        if db_animal_group.animal.current_lot.farm.owner_user_id == current_user.id:
            has_animal_farm_access = True
        else:
            user_farm_accesses = await crud.get_user_farm_accesses_by_user(db, user_id=current_user.id)
            if any(access.farm_id == db_animal_group.animal.current_lot.farm.id for access in user_farm_accesses):
                has_farm_access = True

    is_grupo_creator = db_animal_group.grupo.created_by_user_id == current_user.id

    if not (is_animal_owner or has_animal_farm_access or is_grupo_creator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this animal group association."
        )
    
    success = await crud.delete_animal_group(db, animal_id=animal_id, grupo_id=grupo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Animal Group association not found or could not be deleted")
    return {"message": "Animal Group association deleted successfully"}
