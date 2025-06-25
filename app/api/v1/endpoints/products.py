# app/api/v1/endpoints/products.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response # Importa Response
from sqlalchemy.ext.asyncio import AsyncSession
import uuid # Importa uuid

# --- Importaciones de módulos centrales ---
from app import schemas, models
from app.crud import product as crud_product # Importa la instancia CRUD para product
from app.crud import farm as crud_farm # Importa la instancia CRUD para farm
from app.crud import master_data as crud_master_data # Importa la instancia CRUD para master_data
from app.crud import exceptions as crud_exceptions # Importa tus excepciones CRUD


# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI

# Asumiendo que 'get_db' y 'get_current_active_user' etc. estarán en 'app/api/deps.py'
get_db = deps.get_db
get_current_active_user = deps.get_current_active_user


router = APIRouter(
    prefix="/products", # Añade un prefijo aquí también si no lo tienes en el __init__
    tags=["Products"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_create: schemas.ProductCreate, # Renombrado
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user), # Usar models.User
):
    """
    Crea un nuevo producto en el sistema.
    - Requiere autenticación.
    - El usuario debe ser propietario de la finca especificada.
    - Valida que `product_type_id` y `unit_id` existan en MasterData con las categorías correctas.
    """
    # Verificar que la finca existe y pertenece al usuario actual
    farm = await crud_farm.get(db, id=product_create.farm_id) # Usar crud_farm.get
    if not farm or farm.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Farm not found or you do not have permissions to create products in it."
        )

    # Las validaciones de MasterData (product_type_id y unit_id) se esperan que sean manejadas
    # por el método create del CRUD de Product internamente (en _validate_foreign_keys).
    # Sin embargo, si quieres validación temprana aquí también, puedes añadirla.

    try:
        new_product = await crud_product.create(db, obj_in=product_create, created_by_user_id=current_user.id) # Usar crud_product.create
        return new_product
    except crud_exceptions.NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except crud_exceptions.AlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except crud_exceptions.CRUDException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e}")


@router.get("/{product_id}", response_model=schemas.Product)
async def read_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Obtiene un producto por su ID.
    - Requiere autenticación.
    - El usuario debe ser propietario de la finca a la que pertenece el producto.
    """
    product = await crud_product.get(db, id=product_id) # Usar crud_product.get
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    # Verificar que el producto pertenece a una finca del usuario actual
    farm = await crud_farm.get(db, id=product.farm_id) # Usar crud_farm.get
    if not farm or farm.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permissions to access this product."
        )
    return product

@router.get("/by_farm/{farm_id}", response_model=List[schemas.Product])
async def read_products_by_farm(
    farm_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Obtiene todos los productos asociados a una finca específica.
    - Requiere autenticación.
    - El usuario debe ser propietario de la finca especificada.
    """
    farm = await crud_farm.get(db, id=farm_id) # Usar crud_farm.get
    if not farm or farm.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permissions to access products for this farm."
        )
    products = await crud_product.get_multi_by_farm_id(db, farm_id=farm_id) # Usar crud_product.get_multi_by_farm_id
    return products

@router.put("/{product_id}", response_model=schemas.Product)
async def update_product(
    product_id: uuid.UUID,
    product_update: schemas.ProductUpdate, # Renombrado
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Actualiza un producto existente por su ID.
    - Requiere autenticación.
    - El usuario debe ser propietario de la finca a la que pertenece el producto.
    - Valida que `product_type_id` y `unit_id` existan en MasterData con las categorías correctas si se actualizan.
    """
    product = await crud_product.get(db, id=product_id) # Usar crud_product.get
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    # Verificar que el producto pertenece a una finca del usuario actual
    farm = await crud_farm.get(db, id=product.farm_id) # Usar crud_farm.get
    if not farm or farm.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permissions to update this product."
        )

    # Las validaciones de MasterData (product_type_id y unit_id) se esperan que sean manejadas
    # por el método update del CRUD de Product internamente (_validate_foreign_keys).

    try:
        updated_product = await crud_product.update(db, db_obj=product, obj_in=product_update) # Usar crud_product.update
        return updated_product
    except crud_exceptions.NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except crud_exceptions.AlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except crud_exceptions.CRUDException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e}")


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT) # Cambiado a 204 No Content
async def delete_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Elimina un producto por su ID.
    - Requiere autenticación.
    - El usuario debe ser propietario de la finca a la que pertenece el producto.
    """
    product = await crud_product.get(db, id=product_id) # Usar crud_product.get
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found") # Cambiado "Producto no encontrado" a "Product not found"
    
    # Verificar que el producto pertenece a una finca del usuario actual
    farm = await crud_farm.get(db, id=product.farm_id) # Usar crud_farm.get
    if not farm or farm.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permissions to delete this product."
        )

    try:
        deleted_product = await crud_product.remove(db, id=product_id) # Usa .remove para consistencia con CRUDBase
        if not deleted_product: # crud.remove devuelve el objeto eliminado o None
            raise HTTPException(status_code=404, detail="Product not found or could not be deleted")
        return Response(status_code=status.HTTP_204_NO_CONTENT) # Retorno correcto para 204
    except crud_exceptions.CRUDException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e}")

