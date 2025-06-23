# routers/animals.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Optional

from database import get_db
import schemas
import crud
import models
from dependencies import get_current_user

router = APIRouter(
    prefix="/animals",
    tags=["Animals"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Animal, status_code=status.HTTP_201_CREATED)
async def create_new_animal(
    animal: schemas.AnimalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Crea un nuevo animal.
    Requiere autenticación.
    """
    # 1. Validar que la especie exista y sea un MasterData de categoría 'species'
    if animal.species_id:
        db_species = await crud.get_master_data(db, master_data_id=animal.species_id)
        if not db_species or db_species.category != "species":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Species not found or invalid category."
            )

    # 2. Validar que la raza exista y sea un MasterData de categoría 'breed'
    if animal.breed_id:
        db_breed = await crud.get_master_data(db, master_data_id=animal.breed_id)
        if not db_breed or db_breed.category != "breed":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Breed not found or invalid category."
            )

    # 3. Validar que el lote exista y el usuario tenga acceso a la finca del lote (si current_lot_id es proporcionado)
    if animal.current_lot_id:
        db_lot = await crud.get_lot(db, lot_id=animal.current_lot_id)
        if not db_lot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lot not found."
            )
        # Verificar si el usuario actual es el propietario de la finca a la que pertenece el lote
        if db_lot.farm.owner_user_id != current_user.id:
            # O verificar si el usuario tiene acceso compartido a la finca
            user_farm_accesses = await crud.get_user_farm_accesses_by_user(db, user_id=current_user.id)
            if not any(access.farm_id == db_lot.farm.id for access in user_farm_accesses):
                 raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to assign animals to this lot's farm."
                )

    # 4. Validar que mother_animal_id (si se proporciona) exista y sea un animal válido
    if animal.mother_animal_id: # Solo validar si el ID no es nulo
        db_mother = await crud.get_animal(db, animal_id=animal.mother_animal_id)
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
    if animal.father_animal_id: # Solo validar si el ID no es nulo
        db_father = await crud.get_animal(db, animal_id=animal.father_animal_id)
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
    db_animal = await crud.create_animal(db=db, animal=animal, owner_user_id=current_user.id)
    return db_animal

@router.get("/{animal_id}", response_model=schemas.Animal)
async def read_animal(
    animal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene un animal por su ID.
    El usuario debe ser propietario del animal o tener acceso a la finca del animal.
    """
    db_animal = await crud.get_animal(db, animal_id=animal_id)
    if not db_animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    
    # Verificar si el usuario es dueño del animal
    is_owner = db_animal.owner_user_id == current_user.id

    # Si no es dueño, verificar si tiene acceso a la finca actual del animal (si tiene una)
    has_farm_access = False
    if not is_owner and db_animal.current_lot:
        # Aquí se asume que db_animal.current_lot ya trae db_animal.current_lot.farm cargado
        # gracias a la configuración de selectinload en crud.get_animal.
        if db_animal.current_lot.farm.owner_user_id == current_user.id:
            has_farm_access = True
        else:
            user_farm_accesses = await crud.get_user_farm_accesses_by_user(db, user_id=current_user.id)
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
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene una lista de animales, opcionalmente filtrada por finca y/o lote.
    Solo se devuelven animales a los que el usuario tiene acceso (propiedad o acceso a finca).
    """
    authorized_animal_ids = set()

    # Obtener IDs de fincas del usuario (propietario)
    user_owned_farms = await crud.get_farms_by_owner_id(db, owner_user_id=current_user.id)
    user_owned_farm_ids = {f.id for f in user_owned_farms}

    # Obtener IDs de fincas a las que el usuario tiene acceso compartido
    user_farm_accesses = await crud.get_user_farm_accesses_by_user(db, user_id=current_user.id)
    user_shared_farm_ids = {a.farm_id for a in user_farm_accesses}

    # Combinar todas las fincas a las que el usuario tiene acceso
    all_accessible_farm_ids = user_owned_farm_ids.union(user_shared_farm_ids)

    # Filtrar animales por los parámetros de consulta y acceso
    animals_query_filters = []

    # Filtrar por propietario del animal (el usuario actual)
    # Siempre incluimos los animales de los que el usuario es propietario, sin importar filtros de finca/lote explícitos,
    # a menos que los filtros de finca/lote los excluyan específicamente.
    # Por ahora, nos centraremos en filtrar los animales visibles por finca/lote y propiedad.
    
    # Si se especificó farm_id, debe ser una de las fincas a las que el usuario tiene acceso
    if farm_id:
        if farm_id not in all_accessible_farm_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access animals in this specified farm."
            )
        # Filtraremos en la función CRUD directamente, para evitar cargar todos los lotes primero.
        # animals_query_filters.append(models.Animal.current_lot.has(farm_id=farm_id)) # No funciona directamente así con has() en subrelaciones

    # Si se especificó lot_id, debe pertenecer a una finca a la que el usuario tiene acceso
    if lot_id:
        db_lot = await crud.get_lot(db, lot_id=lot_id)
        if not db_lot or (db_lot.farm.id not in all_accessible_farm_ids):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access animals in this specified lot (or lot not found/accessible)."
            )
        # animals_query_filters.append(models.Animal.current_lot_id == lot_id) # Se usará en crud

    # Obtener animales del usuario, aplicando los filtros de farm_id y lot_id directamente en CRUD
    animals = await crud.get_animals_by_user_and_filters(
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
    current_user: models.User = Depends(get_current_user)
):
    """
    Actualiza un animal existente por su ID.
    El usuario debe ser propietario del animal o tener acceso a la finca del animal.
    """
    db_animal = await crud.get_animal(db, animal_id=animal_id)
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
            user_farm_accesses = await crud.get_user_farm_accesses_by_user(db, user_id=current_user.id)
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
        db_species = await crud.get_master_data(db, master_data_id=animal_update.species_id)
        if not db_species or db_species.category != "species":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New species not found or invalid.")

    # Si se actualiza la raza
    if animal_update.breed_id and animal_update.breed_id != db_animal.breed_id:
        db_breed = await crud.get_master_data(db, master_data_id=animal_update.breed_id)
        if not db_breed or db_breed.category != "breed":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New breed not found or invalid.")

    # Si se actualiza el lote actual
    if animal_update.current_lot_id is not None and animal_update.current_lot_id != db_animal.current_lot_id:
        db_new_lot = await crud.get_lot(db, lot_id=animal_update.current_lot_id)
        if not db_new_lot:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New lot not found.")
        # Verificar acceso a la nueva finca del lote
        if db_new_lot.farm.owner_user_id != current_user.id:
            user_farm_accesses = await crud.get_user_farm_accesses_by_user(db, user_id=current_user.id)
            if not any(access.farm_id == db_new_lot.farm.id for access in user_farm_accesses):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to assign animal to this new lot's farm."
                )
    
    # Validar mother_animal_id si se actualiza y no es nulo
    if animal_update.mother_animal_id is not None and animal_update.mother_animal_id != db_animal.mother_animal_id:
        db_new_mother = await crud.get_animal(db, animal_id=animal_update.mother_animal_id)
        if not db_new_mother:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New mother animal not found.")
        if db_new_mother.owner_user_id != current_user.id: # O verificar acceso a la finca de la madre
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to use this animal as new mother.")

    # Validar father_animal_id si se actualiza y no es nulo
    if animal_update.father_animal_id is not None and animal_update.father_animal_id != db_animal.father_animal_id:
        db_new_father = await crud.get_animal(db, animal_id=animal_update.father_animal_id)
        if not db_new_father:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New father animal not found.")
        if db_new_father.owner_user_id != current_user.id: # O verificar acceso a la finca del padre
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to use this animal as new father.")

    updated_animal = await crud.update_animal(db, animal_id=animal_id, animal_update=animal_update)
    return updated_animal

@router.delete("/{animal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_animal(
    animal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Elimina un animal por su ID.
    El usuario debe ser propietario del animal.
    """
    db_animal = await crud.get_animal(db, animal_id=animal_id)
    if not db_animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    
    # Solo el propietario del animal puede eliminarlo
    if db_animal.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this animal."
        )
    
    success = await crud.delete_animal(db, animal_id=animal_id)
    if not success:
        raise HTTPException(status_code=404, detail="Animal not found or could not be deleted")
    return {"message": "Animal deleted successfully"}

