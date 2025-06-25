# app/api/v1/endpoints/animals.py
from fastapi import APIRouter, Depends, HTTPException, status, Response # Importa Response
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Optional

# --- Importaciones de módulos centrales ---
from app import schemas, models
from app.crud import animal as crud_animal # Importa la instancia CRUD para animal
from app.crud import master_data as crud_master_data # Importa la instancia CRUD para master_data
from app.crud import lot as crud_lot # Importa la instancia CRUD para lot
from app.crud import user_farm_access as crud_user_farm_access # Importa la instancia CRUD para user_farm_access
from app.crud import farm as crud_farm # Importa la instancia CRUD para farm

# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI

# Asumiendo que 'get_db', 'get_current_active_user' etc. estarán en 'app/api/deps.py'
get_db = deps.get_db
get_current_active_user = deps.get_current_active_user


router = APIRouter(
    prefix="/animals",
    tags=["Animals"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Animal, status_code=status.HTTP_201_CREATED)
async def create_new_animal(
    animal_in: schemas.AnimalCreate, # Renombrado a animal_in
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Crea un nuevo animal.
    Requiere autenticación.
    """
    # 1. Validar que la especie exista y sea un MasterData de categoría 'species'
    if animal_in.species_id:
        db_species = await crud_master_data.get(db, id=animal_in.species_id) # Usar crud_master_data
        if not db_species or db_species.category != "species":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Species not found or invalid category."
            )

    # 2. Validar que la raza exista y sea un MasterData de categoría 'breed'
    if animal_in.breed_id:
        db_breed = await crud_master_data.get(db, id=animal_in.breed_id) # Usar crud_master_data
        if not db_breed or db_breed.category != "breed":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Breed not found or invalid category."
            )

    # 3. Validar que el lote exista y el usuario tenga acceso a la finca del lote (si current_lot_id es proporcionado)
    if animal_in.current_lot_id:
        db_lot = await crud_lot.get(db, id=animal_in.current_lot_id) # Usar crud_lot
        if not db_lot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lot not found."
            )
        # Verificar si el usuario actual es el propietario de la finca a la que pertenece el lote
        if db_lot.farm.owner_user_id != current_user.id:
            # O verificar si el usuario tiene acceso compartido a la finca
            user_farm_accesses = await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id) # Usar crud_user_farm_access
            if not any(access.farm_id == db_lot.farm.id for access in user_farm_accesses):
                 raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to assign animals to this lot's farm."
                )

    # 4. Validar que mother_animal_id (si se proporciona) exista y sea un animal válido
    if animal_in.mother_animal_id: # Solo validar si el ID no es nulo
        db_mother = await crud_animal.get(db, id=animal_in.mother_animal_id) # Usar crud_animal
        if not db_mother:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mother animal not found."
            )
        # Opcional: Verificar si el usuario tiene acceso a la madre también.
        if db_mother.owner_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to use this animal as mother."
            )

    # 5. Validar que father_animal_id (si se proporciona) exista y sea un animal válido
    if animal_in.father_animal_id: # Solo validar si el ID no es nulo
        db_father = await crud_animal.get(db, id=animal_in.father_animal_id) # Usar crud_animal
        if not db_father:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Father animal not found."
            )
        # Opcional: Verificar si el usuario tiene acceso al padre también.
        if db_father.owner_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to use this animal as father."
            )

    # 6. Crear el animal, asignándolo al usuario actual como propietario
    db_animal = await crud_animal.create(db=db, obj_in=animal_in, owner_user_id=current_user.id) # Usar crud_animal
    return db_animal

@router.get("/{animal_id}", response_model=schemas.Animal)
async def read_animal(
    animal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtiene un animal por su ID.
    El usuario debe ser propietario del animal o tener acceso a la finca del animal.
    """
    db_animal = await crud_animal.get(db, id=animal_id) # Usar crud_animal
    if not db_animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    
    # Verificar si el usuario es dueño del animal
    is_owner = db_animal.owner_user_id == current_user.id

    # Si no es dueño, verificar si tiene acceso a la finca actual del animal (si tiene una)
    has_farm_access = False
    if not is_owner and db_animal.current_lot:
        # Asegúrate de que db_animal.current_lot.farm esté cargado por el CRUD
        if db_animal.current_lot.farm.owner_user_id == current_user.id:
            has_farm_access = True
        else:
            user_farm_accesses = await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id) # Usar crud_user_farm_access
            if any(access.farm_id == db_animal.current_lot.farm.id for access in user_farm_accesses):
                has_farm_access = True

    if not (is_owner or has_farm_access):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this animal."
        )
    return db_animal

@router.get("/", response_model=List[schemas.Animal])
async def read_animals(
    skip: int = 0, 
    limit: int = 100,
    farm_id: Optional[uuid.UUID] = None, # Filtro opcional por finca
    lot_id: Optional[uuid.UUID] = None,  # Filtro opcional por lote
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtiene una lista de animales, opcionalmente filtrada por finca y/o lote.
    Solo se devuelven animales a los que el usuario tiene acceso (propiedad o acceso a finca).
    """
    # Obtener IDs de fincas del usuario (propietario)
    user_owned_farms = await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id) # Usar crud_farm
    user_owned_farm_ids = {f.id for f in user_owned_farms}

    # Obtener IDs de fincas a las que el usuario tiene acceso compartido
    user_farm_accesses = await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id) # Usar crud_user_farm_access
    user_shared_farm_ids = {a.farm_id for a in user_farm_accesses}

    # Combinar todas las fincas a las que el usuario tiene acceso
    all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

    # Si se especificó farm_id, debe ser una de las fincas a las que el usuario tiene acceso
    if farm_id and farm_id not in all_accessible_farm_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access animals in this specified farm."
        )

    # Si se especificó lot_id, debe pertenecer a una finca a la que el usuario tiene acceso
    if lot_id:
        db_lot = await crud_lot.get(db, id=lot_id) # Usar crud_lot
        if not db_lot or (db_lot.farm.id not in all_accessible_farm_ids):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access animals in this specified lot (or lot not found/accessible)."
            )

    # Obtener animales del usuario, aplicando los filtros de farm_id y lot_id directamente en CRUD
    # Se asume que crud.animal.get_animals_by_user_and_filters existe y maneja la lógica de autorización
    # Si no existe, deberías implementarlo en app/crud/animals.py
    animals = await crud_animal.get_animals_by_user_and_filters(
        db, 
        user_id=current_user.id, 
        farm_id=farm_id, 
        lot_id=lot_id, 
        accessible_farm_ids=list(all_accessible_farm_ids), # Pasar la lista de IDs de fincas accesibles
        skip=skip, 
        limit=limit
    )
    
    return animals


@router.put("/{animal_id}", response_model=schemas.Animal)
async def update_existing_animal(
    animal_id: uuid.UUID,
    animal_update: schemas.AnimalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Actualiza un animal existente por su ID.
    El usuario debe ser propietario del animal o tener acceso a la finca del animal.
    """
    db_animal = await crud_animal.get(db, id=animal_id) # Usar crud_animal
    if not db_animal:
        raise HTTPException(status_code=404, detail="Animal not found")

    # Verificar si el usuario es dueño del animal
    is_owner = db_animal.owner_user_id == current_user.id

    # Si no es dueño, verificar si tiene acceso a la finca actual del animal (si tiene una)
    has_farm_access = False
    if not is_owner and db_animal.current_lot:
        if db_animal.current_lot.farm.owner_user_id == current_user.id:
            has_farm_access = True
        else:
            user_farm_accesses = await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id) # Usar crud_user_farm_access
            if any(access.farm_id == db_animal.current_lot.farm.id for access in user_farm_accesses):
                has_farm_access = True
    
    if not (is_owner or has_farm_access):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this animal."
        )

    # Validaciones adicionales para los campos que se pueden actualizar:
    # Si se actualiza la especie
    if animal_update.species_id and animal_update.species_id != db_animal.species_id:
        db_species = await crud_master_data.get(db, id=animal_update.species_id) # Usar crud_master_data
        if not db_species or db_species.category != "species":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New species not found or invalid.")

    # Si se actualiza la raza
    if animal_update.breed_id and animal_update.breed_id != db_animal.breed_id:
        db_breed = await crud_master_data.get(db, id=animal_update.breed_id) # Usar crud_master_data
        if not db_breed or db_breed.category != "breed":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New breed not found or invalid.")

    # Si se actualiza el lote actual
    if animal_update.current_lot_id is not None and animal_update.current_lot_id != db_animal.current_lot_id:
        db_new_lot = await crud_lot.get(db, id=animal_update.current_lot_id) # Usar crud_lot
        if not db_new_lot:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New lot not found.")
        # Verificar acceso a la nueva finca del lote
        if db_new_lot.farm.owner_user_id != current_user.id:
            user_farm_accesses = await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id) # Usar crud_user_farm_access
            if not any(access.farm_id == db_new_lot.farm.id for access in user_farm_accesses):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to assign animal to this new lot's farm."
                )
    
    # Validar mother_animal_id si se actualiza y no es nulo
    if animal_update.mother_animal_id is not None and animal_update.mother_animal_id != db_animal.mother_animal_id:
        db_new_mother = await crud_animal.get(db, id=animal_update.mother_animal_id) # Usar crud_animal
        if not db_new_mother:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New mother animal not found.")
        # Se debería verificar el acceso a la madre si no es propiedad del usuario,
        # similar a la lógica de acceso para el animal principal.
        if db_new_mother.owner_user_id != current_user.id:
            # Obtener acceso a fincas del usuario
            user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
            user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
            all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)
            
            has_access_to_mother_farm = False
            if db_new_mother.current_lot and db_new_mother.current_lot.farm:
                if db_new_mother.current_lot.farm.id in all_accessible_farm_ids:
                    has_access_to_mother_farm = True

            if not has_access_to_mother_farm:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to use this animal as new mother.")


    # Validar father_animal_id si se actualiza y no es nulo
    if animal_update.father_animal_id is not None and animal_update.father_animal_id != db_animal.father_animal_id:
        db_new_father = await crud_animal.get(db, id=animal_update.father_animal_id) # Usar crud_animal
        if not db_new_father:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New father animal not found.")
        # Se debería verificar el acceso al padre si no es propiedad del usuario.
        if db_new_father.owner_user_id != current_user.id:
            user_owned_farm_ids = {f.id for f in await crud_farm.get_farms_by_owner(db, owner_user_id=current_user.id)}
            user_shared_farm_ids = {a.farm_id for a in await crud_user_farm_access.get_user_farm_accesses(db, user_id=current_user.id)}
            all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)
            
            has_access_to_father_farm = False
            if db_new_father.current_lot and db_new_father.current_lot.farm:
                if db_new_father.current_lot.farm.id in all_accessible_farm_ids:
                    has_access_to_father_farm = True
            
            if not has_access_to_father_farm:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to use this animal as new father.")


    updated_animal = await crud_animal.update(db, db_obj=db_animal, obj_in=animal_update) # Usar crud_animal
    return updated_animal

@router.delete("/{animal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_animal(
    animal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Elimina un animal por su ID.
    El usuario debe ser propietario del animal.
    """
    db_animal = await crud_animal.get(db, id=animal_id) # Usar crud_animal
    if not db_animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    
    # Solo el propietario del animal puede eliminarlo
    if db_animal.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this animal."
        )
    
    deleted_animal = await crud_animal.remove(db, id=animal_id) # Usar crud_animal
    if not deleted_animal:
        raise HTTPException(status_code=404, detail="Animal not found or could not be deleted")
    return Response(status_code=status.HTTP_204_NO_CONTENT) # Retorno correcto para 204

