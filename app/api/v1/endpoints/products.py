        # app/api/v1/endpoints/products.py
        from typing import List
        from fastapi import APIRouter, Depends, HTTPException, status
        from sqlalchemy.ext.asyncio import AsyncSession
        import uuid # Importa uuid

        # --- Importaciones de módulos centrales ---
        from app import crud, schemas, models # Acceso de alto nivel a tus módulos principales

        # --- Importaciones de dependencias y seguridad ---
        from app.api import deps # Acceso a las dependencias de FastAPI (get_db, get_current_user, etc.)

        router = APIRouter()

        @router.post("/", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
        async def create_product(
            product_in: schemas.ProductCreate,
            db: AsyncSession = Depends(deps.get_db),
            current_user: schemas.User = Depends(deps.get_current_active_user), # Usar schemas.User según tu User model
        ):
            """
            Crea un nuevo producto en el sistema.
            - Requiere autenticación.
            - El usuario debe ser propietario de la finca especificada.
            - Valida que `product_type_id` y `unit_id` existan en MasterData con las categorías correctas.
            """
            # Verificar que la finca existe y pertenece al usuario actual (o tiene permisos)
            farm = await crud.farm.get(db, product_in.farm_id)
            if not farm or farm.owner_user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Farm not found or you do not have permissions to create products in it."
                )

            try:
                new_product = await crud.product.create(db, obj_in=product_in, created_by_user_id=current_user.id)
                return new_product
            except crud.exceptions.NotFoundError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            except crud.exceptions.AlreadyExistsError as e:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
            except crud.exceptions.CRUDException as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e}")


        @router.get("/{product_id}", response_model=schemas.Product)
        async def read_product(
            product_id: uuid.UUID, # Cambiado a uuid.UUID
            db: AsyncSession = Depends(deps.get_db),
            current_user: schemas.User = Depends(deps.get_current_active_user),
        ):
            """
            Obtiene un producto por su ID.
            - Requiere autenticación.
            - El usuario debe ser propietario de la finca a la que pertenece el producto.
            """
            product = await crud.product.get(db, product_id)
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
            
            # Verificar que el producto pertenece a una finca del usuario actual
            farm = await crud.farm.get(db, product.farm_id)
            if not farm or farm.owner_user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permissions to access this product."
                )
            return product

        @router.get("/by_farm/{farm_id}", response_model=List[schemas.Product])
        async def read_products_by_farm(
            farm_id: uuid.UUID, # Cambiado a uuid.UUID
            db: AsyncSession = Depends(deps.get_db),
            current_user: schemas.User = Depends(deps.get_current_active_user),
        ):
            """
            Obtiene todos los productos asociados a una finca específica.
            - Requiere autenticación.
            - El usuario debe ser propietario de la finca especificada.
            """
            farm = await crud.farm.get(db, farm_id)
            if not farm or farm.owner_user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permissions to access products for this farm."
                )
            products = await crud.product.get_multi_by_farm_id(db, farm_id=farm_id)
            return products

        @router.put("/{product_id}", response_model=schemas.Product)
        async def update_product(
            product_id: uuid.UUID, # Cambiado a uuid.UUID
            product_in: schemas.ProductUpdate,
            db: AsyncSession = Depends(deps.get_db),
            current_user: schemas.User = Depends(deps.get_current_active_user),
        ):
            """
            Actualiza un producto existente por su ID.
            - Requiere autenticación.
            - El usuario debe ser propietario de la finca a la que pertenece el producto.
            - Valida que `product_type_id` y `unit_id` existan en MasterData con las categorías correctas si se actualizan.
            """
            product = await crud.product.get(db, product_id)
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
            
            # Verificar que el producto pertenece a una finca del usuario actual
            farm = await crud.farm.get(db, product.farm_id)
            if not farm or farm.owner_user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permissions to update this product."
                )

            try:
                updated_product = await crud.product.update(db, db_obj=product, obj_in=product_in)
                return updated_product
            except crud.exceptions.NotFoundError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            except crud.exceptions.AlreadyExistsError as e:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
            except crud.exceptions.CRUDException as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e}")


        @router.delete("/{product_id}", response_model=schemas.Product)
        async def delete_product(
            product_id: uuid.UUID, # Cambiado a uuid.UUID
            db: AsyncSession = Depends(deps.get_db),
            current_user: schemas.User = Depends(deps.get_current_active_user),
        ):
            """
            Elimina un producto por su ID.
            - Requiere autenticación.
            - El usuario debe ser propietario de la finca a la que pertenece el producto.
            """
            product = await crud.product.get(db, product_id)
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
            
            # Verificar que el producto pertenece a una finca del usuario actual
            farm = await crud.farm.get(db, product.farm_id)
            if not farm or farm.owner_user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permissions to delete this product."
                )

            try:
                deleted_product = await crud.product.delete(db, id=product_id) # Usa .delete en lugar de .remove
                return deleted_product
            except crud.exceptions.CRUDException as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e}")
        