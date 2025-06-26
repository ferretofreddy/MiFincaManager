# app/api/v1/endpoints/farms.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List

# --- Importaciones de módulos centrales ---
from app import schemas, models
from app.crud import farm as crud_farm

# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI (incluido has_permission)

# Asumiendo que 'get_db' y 'get_current_active_user' están en 'app/api/deps.py'
get_db = deps.get_db
get_current_active_user = deps.get_current_active_user
get_current_active_superuser = deps.get_current_active_superuser # Para superusuarios

router = APIRouter(
    prefix="/farms",
    tags=["Farms"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Farm, status_code=status.HTTP_201_CREATED)
async def create_new_farm(
    farm_in: schemas.FarmCreate,
    db: AsyncSession = Depends(get_db),
    # Requiere el permiso 'farm:create' para crear una finca
    current_user: models.User = Depends(deps.has_permission("farm:create")) 
):
    """
    Crea una nueva finca para el usuario autenticado.
    Requiere el permiso 'farm:create'.
    """
    # Usar la instancia crud.farm
    return await crud_farm.create(db=db, obj_in=farm_in, owner_user_id=current_user.id)

@router.get("/{farm_id}", response_model=schemas.Farm)
async def read_farm(
    farm_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    # Requiere el permiso 'farm:read' para leer una finca
    current_user: models.User = Depends(deps.has_permission("farm:read")) 
):
    """
    Obtiene una finca por su ID. Solo si el usuario autenticado es el propietario
    o si tiene el permiso 'farm:read' (un superusuario lo tendrá, o un rol asignado).
    """
    db_farm = await crud_farm.get(db, id=farm_id)
    if db_farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    # Lógica de autorización adicional: el propietario siempre puede ver su finca.
    # Si el usuario no es el propietario, la dependencia 'has_permission' ya habrá verificado
    # si tiene el permiso 'farm:read' globalmente o a través de sus roles.
    if db_farm.owner_user_id != current_user.id and not current_user.is_superuser:
        # Aquí, si el current_user no es el propietario y no es superuser,
        # y no pasó el 'farm:read' (que ya se verificó), entonces 403.
        # La dependencia ya maneja el caso de falta de permiso.
        # Si llega aquí, significa que el 'farm:read' se verificó, pero
        # la finca no es del usuario. Podríamos requerir un permiso más específico
        # como 'farm:read_all' si el 'farm:read' es solo para las propias fincas.
        # Por ahora, si has_permission("farm:read") permite, dejamos pasar.
        # Ajusta esta lógica si "farm:read" implica SÓLO sus propias fincas.
        # Para este ejemplo, 'farm:read' otorga ver *cualquier* finca.
        # Si solo quieres que el propietario vea la suya, remueve el `has_permission` de aquí
        # y deja `current_user: models.User = Depends(get_current_active_user)` y la verificación `db_farm.owner_user_id != current_user.id`.
        pass # La lógica de acceso está cubierta por el permiso y la verificación de propiedad si aplica.

    # Si el usuario no es el propietario, y no es superusuario, pero tiene 'farm:read'
    # puede verla. Si el permiso 'farm:read' debe ser solo para las fincas del usuario,
    # la lógica de 'has_permission' debería ser más granular o se debería manejar aquí.
    # Por ahora, asumo que 'farm:read' es permiso general para ver fincas.
    if db_farm.owner_user_id != current_user.id and not current_user.is_superuser:
        # En este punto, si current_user llegó hasta acá, es porque tiene 'farm:read'.
        # Si además de 'farm:read', quieres que solo VEA sus fincas, entonces esta línea
        # sería: if db_farm.owner_user_id != current_user.id: raise HTTPException(...)
        # La forma actual asume que 'farm:read' es un permiso más amplio.
        # Si se necesita granularidad, se crearían permisos como 'farm:read_own' y 'farm:read_all'.
        pass

    return db_farm

@router.get("/", response_model=List[schemas.Farm])
async def read_farms(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    # Requiere el permiso 'farm:read_all' para listar todas las fincas
    current_user: models.User = Depends(deps.has_permission("farm:read_all")) 
):
    """
    Obtiene una lista de fincas. Si el usuario es propietario o tiene acceso granular,
    debería ver las suyas. Si tiene 'farm:read_all', verá todas.
    """
    # En este punto, el usuario ya tiene 'farm:read_all' o es superusuario.
    # Si quisieras que los usuarios no-superusuarios solo vieran sus fincas aunque
    # tuvieran 'farm:read_all' (lo cual sería contradictorio), la lógica aquí cambiaría.
    # Asumo que 'farm:read_all' es para ver todas.
    farms = await crud_farm.get_multi(db, skip=skip, limit=limit) # Obtiene todas las fincas
    return farms


@router.put("/{farm_id}", response_model=schemas.Farm)
async def update_existing_farm(
    farm_id: uuid.UUID,
    farm_update: schemas.FarmUpdate,
    db: AsyncSession = Depends(get_db),
    # Requiere el permiso 'farm:update' para actualizar una finca
    current_user: models.User = Depends(deps.has_permission("farm:update")) 
):
    """
    Actualiza una finca existente por su ID.
    Requiere el permiso 'farm:update' y ser el propietario de la finca o superusuario.
    """
    db_farm = await crud_farm.get(db, id=farm_id)
    if db_farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    # Adicionalmente a tener el permiso, el usuario debe ser el propietario de la finca
    # a menos que sea un superusuario que pueda actualizar cualquier cosa.
    if db_farm.owner_user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this farm: you are not the owner."
        )
    
    updated_farm = await crud_farm.update(db, db_obj=db_farm, obj_in=farm_update)
    return updated_farm

@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_farm(
    farm_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    # Requiere el permiso 'farm:delete' para eliminar una finca
    current_user: models.User = Depends(deps.has_permission("farm:delete")) 
):
    """
    Elimina una finca por su ID.
    Requiere el permiso 'farm:delete' y ser el propietario de la finca o superusuario.
    """
    db_farm = await crud_farm.get(db, id=farm_id)
    if db_farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    # Adicionalmente a tener el permiso, el usuario debe ser el propietario de la finca
    # a menos que sea un superusuario que pueda eliminar cualquier cosa.
    if db_farm.owner_user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this farm: you are not the owner."
        )
    
    deleted_farm = await crud_farm.remove(db, id=farm_id)
    if not deleted_farm:
        raise HTTPException(status_code=404, detail="Farm not found or could not be deleted")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

