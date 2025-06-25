# app/api/v1/endpoints/animal_groups.py
from fastapi import APIRouter, Depends, HTTPException, status, Response # Importa Response
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Optional

# --- Importaciones de módulos centrales ---
from app import schemas, models
from app.crud import animal_group as crud_animal_group
from app.crud import animal as crud_animal
from app.crud import grupo as crud_grupo
from app.crud import user_farm_access as crud_user_farm_access
from app.crud import farm as crud_farm


# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI

get_db = deps.get_db
get_current_active_user = deps.get_current_active_user


router = APIRouter(
    prefix="/animal-groups",
    tags=["Animal Groups"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.AnimalGroup, status_code=status.HTTP_201_CREATED)
async def create_new_animal_group(
    animal_group_in: schemas.AnimalGroupCreate, # Renombrado
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Asocia un animal a un grupo.
    Requiere autenticación.
    Verifica que el animal y el grupo existan y que el usuario tenga acceso a ellos.
    También verifica que la asociación no exista previamente.
    """
    # 1. Verificar que el animal exista y el usuario sea propietario o tenga acceso a su finca
    db_animal = await crud_animal.get(db, id=animal_group_in.animal_id) # Usar crud_animal
    if not db_animal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Animal not found."
        )
    
    is_animal_owner = db_animal.owner_user_id == current_user.id
    has_animal_farm_access = False
    if not is_animal_owner and db_animal.current_lot:
        # Asegúrate de que db_animal.current_lot.farm esté cargado por el CRUD de animal
        if db_animal.current_lot.farm.owner_user_id == current_user.id:
            has_animal_farm_access = True
        else:
            user_farm_accesses = await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id) # Usar crud_user_farm_access
            if any(access.farm_id == db_animal.current_lot.farm.id for access in user_farm_accesses):
                has_animal_farm_access = True
    
    if not (is_animal_owner or has_animal_farm_access):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to associate this animal."
        )

    # 2. Verificar que el grupo exista y el usuario sea quien lo creó
    db_grupo = await crud_grupo.get(db, id=animal_group_in.grupo_id) # Usar crud_grupo
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

    # 3. Verificar si la asociación ya existe (asumiendo que solo hay una activa por animal-grupo)
    # Si quieres permitir múltiples asociaciones históricas, esta verificación cambiaría.
    existing_animal_group = await crud_animal_group.get_by_compound_keys(
        db, 
        animal_id=animal_group_in.animal_id, 
        grupo_id=animal_group_in.grupo_id,
        assigned_at=animal_group_in.assigned_at # Incluir assigned_at para unicidad compuesta
    )
    if existing_animal_group:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Animal is already associated with this group at this time."
        )

    # 4. Crear la asociación
    db_animal_group = await crud_animal_group.create(db=db, obj_in=animal_group_in, created_by_user_id=current_user.id) # Usar crud_animal_group
    return db_animal_group

@router.get("/", response_model=List[schemas.AnimalGroup])
async def read_animal_groups(
    skip: int = 0,
    limit: int = 100,
    animal_id: Optional[uuid.UUID] = None,
    grupo_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtiene una lista de asociaciones animal-grupo.
    Permite filtrar por animal_id o grupo_id.
    Solo muestra asociaciones donde el usuario tiene acceso al animal O ha creado el grupo.
    """
    # Lógica de filtrado y autorización combinada.
    # Obtener IDs de fincas del usuario (propietario)
    user_owned_farms = await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id) # Usar crud_farm
    user_owned_farm_ids = {f.id for f in user_owned_farms}

    # Obtener IDs de fincas a las que el usuario tiene acceso compartido
    user_farm_accesses = await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id) # Usar crud_user_farm_access
    user_shared_farm_ids = {a.farm_id for a in user_farm_accesses}

    # Combinar todas las fincas a las que el usuario tiene acceso
    all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

    # Obtener IDs de grupos creados por el usuario
    user_created_grupos = await crud_grupo.get_multi_by_created_by_user_id(db, created_by_user_id=current_user.id) # Usar crud_grupo
    user_created_grupo_ids = {g.id for g in user_created_grupos}

    # Filtrar las asociaciones directamente en el CRUD para eficiencia
    # Necesitas un método como 'get_multi_by_filters_and_access' en crud.animal_group
    animal_groups = await crud_animal_group.get_multi_by_filters_and_access(
        db,
        animal_id=animal_id,
        grupo_id=grupo_id,
        current_user_id=current_user.id,
        accessible_farm_ids=list(all_accessible_farm_ids),
        user_created_grupo_ids=list(user_created_grupo_ids),
        skip=skip,
        limit=limit
    )
    return animal_groups

@router.get("/{animal_group_id}", response_model=schemas.AnimalGroup) # Cambio de /{animal_id}/{grupo_id}
async def read_single_animal_group(
    animal_group_id: uuid.UUID, # Ahora se busca por el ID único de AnimalGroup
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtiene una asociación animal-grupo específica por su ID único.
    El usuario debe tener acceso al animal O haber creado el grupo.
    """
    db_animal_group = await crud_animal_group.get(db, id=animal_group_id) # Usar crud_animal_group.get
    if not db_animal_group:
        raise HTTPException(status_code=404, detail="Animal Group association not found")
    
    # Verificar acceso al animal
    is_animal_owner = db_animal_group.animal.owner_user_id == current_user.id
    has_animal_farm_access = False
    if not is_animal_owner and db_animal_group.animal.current_lot:
        if db_animal_group.animal.current_lot.farm.owner_user_id == current_user.id:
            has_animal_farm_access = True
        else:
            user_farm_accesses = await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id) # Usar crud_user_farm_access
            if any(access.farm_id == db_animal_group.animal.current_lot.farm.id for access in user_farm_accesses):
                has_animal_farm_access = True

    # Verificar si el usuario creó el grupo
    is_grupo_creator = db_animal_group.grupo.created_by_user_id == current_user.id

    if not (is_animal_owner or has_animal_farm_access or is_grupo_creator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this animal group association."
        )
    return db_animal_group

@router.put("/{animal_group_id}", response_model=schemas.AnimalGroup) # Cambio a ID único
async def update_existing_animal_group(
    animal_group_id: uuid.UUID, # Ahora se busca por el ID único
    animal_group_update: schemas.AnimalGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Actualiza una asociación animal-grupo existente por su ID único.
    El usuario debe tener acceso al animal O haber creado el grupo para actualizarlo.
    """
    db_animal_group = await crud_animal_group.get(db, id=animal_group_id) # Usar crud_animal_group.get
    if not db_animal_group:
        raise HTTPException(status_code=404, detail="Animal Group association not found")

    # Verificar acceso al animal o ser creador del grupo para permitir la actualización
    is_animal_owner = db_animal_group.animal.owner_user_id == current_user.id
    has_animal_farm_access = False
    if not is_animal_owner and db_animal_group.animal.current_lot:
        if db_animal_group.animal.current_lot.farm.owner_user_id == current_user.id:
            has_animal_farm_access = True
        else:
            user_farm_accesses = await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id) # Usar crud_user_farm_access
            if any(access.farm_id == db_animal_group.animal.current_lot.farm.id for access in user_farm_accesses):
                has_farm_access = True

    is_grupo_creator = db_animal_group.grupo.created_by_user_id == current_user.id

    if not (is_animal_owner or has_animal_farm_access or is_grupo_creator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this animal group association."
        )
    
    updated_animal_group = await crud_animal_group.update(db, db_obj=db_animal_group, obj_in=animal_group_update) # Usar crud_animal_group.update
    return updated_animal_group

@router.delete("/{animal_group_id}", status_code=status.HTTP_204_NO_CONTENT) # Cambio a ID único
async def delete_existing_animal_group(
    animal_group_id: uuid.UUID, # Ahora se busca por el ID único
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Elimina una asociación animal-grupo por su ID único.
    El usuario debe tener acceso al animal O haber creado el grupo para eliminarlo.
    """
    db_animal_group = await crud_animal_group.get(db, id=animal_group_id) # Usar crud_animal_group.get
    if not db_animal_group:
        raise HTTPException(status_code=404, detail="Animal Group association not found")

    # Verificar acceso al animal o ser creador del grupo para permitir la eliminación
    is_animal_owner = db_animal_group.animal.owner_user_id == current_user.id
    has_animal_farm_access = False
    if not is_animal_owner and db_animal_group.animal.current_lot:
        if db_animal_group.animal.current_lot.farm.owner_user_id == current_user.id:
            has_animal_farm_access = True
        else:
            user_farm_accesses = await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id) # Usar crud_user_farm_access
            if any(access.farm_id == db_animal_group.animal.current_lot.farm.id for access in user_farm_accesses):
                has_farm_access = True

    is_grupo_creator = db_animal_group.grupo.created_by_user_id == current_user.id

    if not (is_animal_owner or has_animal_farm_access or is_grupo_creator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this animal group association."
        )
    
    deleted_animal_group = await crud_animal_group.remove(db, id=animal_group_id) # Usar crud_animal_group.remove
    if not deleted_animal_group:
        raise HTTPException(status_code=404, detail="Animal Group association not found or could not be deleted")
    return Response(status_code=status.HTTP_204_NO_CONTENT) # Retorno correcto para 204

