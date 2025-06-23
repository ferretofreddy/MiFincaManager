        # app/api/v1/endpoints/products.py
        from typing import List
        from fastapi import APIRouter, Depends, HTTPException, status
        from sqlalchemy.ext.asyncio import AsyncSession

        from app import crud, schemas
        from app.api import deps

        router = APIRouter()

        @router.post("/", response_model=schemas.ProductInDB, status_code=status.HTTP_201_CREATED)
        async def create_product(
            product_in: schemas.ProductCreate,
            db: AsyncSession = Depends(deps.get_db),
            current_user: schemas.UserInDB = Depends(deps.get_current_active_user),
        ):
            """
            Creates a new product in the system.
            """
            # Verify that product_type_id and unit_id exist in MasterData and are of the correct type
            product_type = await crud.master_data.get(db, product_in.product_type_id)
            if not product_type or product_type.category != "product_type":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid product type. It must be a MasterData entry with category 'product_type'."
                )
            
            unit = await crud.master_data.get(db, product_in.unit_id)
            if not unit or unit.category != "unit_of_measure": # Assuming you use 'unit_of_measure' as category
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid unit of measure. It must be a MasterData entry with category 'unit_of_measure'."
                )

            # Ensure that the farm exists and belongs to the current user (or has permissions)
            farm = await crud.farm.get(db, product_in.farm_id)
            if not farm or farm.created_by_user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Farm not found or you do not have permissions to create products on it."
                )

            product_data = product_in.model_dump()
            product_data["created_by_user_id"] = current_user.id
            
            new_product = await crud.product.create(db, obj_in=product_data)
            return new_product

        @router.get("/{product_id}", response_model=schemas.ProductInDB)
        async def read_product(
            product_id: int,
            db: AsyncSession = Depends(deps.get_db),
            current_user: schemas.UserInDB = Depends(deps.get_current_active_user),
        ):
            """
            Gets a product by its ID.
            """
            product = await crud.product.get(db, product_id)
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
            # Verify that the product belongs to a farm of the current user
            farm = await crud.farm.get(db, product.farm_id)
            if not farm or farm.created_by_user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permissions to access this product."
                )
            return product

        @router.get("/by_farm/{farm_id}", response_model=List[schemas.ProductInDB])
        async def read_products_by_farm(
            farm_id: int,
            db: AsyncSession = Depends(deps.get_db),
            current_user: schemas.UserInDB = Depends(deps.get_current_active_user),
        ):
            """
            Gets all products associated with a specific farm.
            """
            farm = await crud.farm.get(db, farm_id)
            if not farm or farm.created_by_user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permissions to access products for this farm."
                )
            products = await crud.product.get_by_farm_id(db, farm_id=farm_id)
            return products

        @router.put("/{product_id}", response_model=schemas.ProductInDB)
        async def update_product(
            product_id: int,
            product_in: schemas.ProductUpdate,
            db: AsyncSession = Depends(deps.get_db),
            current_user: schemas.UserInDB = Depends(deps.get_current_active_user),
        ):
            """
            Updates an existing product by its ID.
            """
            product = await crud.product.get(db, product_id)
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
            
            # Verify that the product belongs to a farm of the current user
            farm = await crud.farm.get(db, product.farm_id)
            if not farm or farm.created_by_user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permissions to update this product."
                )

            # Optional: Validate if product_type_id or unit_id are updated
            if product_in.product_type_id:
                product_type = await crud.master_data.get(db, product_in.product_type_id)
                if not product_type or product_type.category != "product_type":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid product type. It must be a MasterData entry with category 'product_type'."
                    )
            if product_in.unit_id:
                unit = await crud.master_data.get(db, product_in.unit_id)
                if not unit or unit.category != "unit_of_measure":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid unit of measure. It must be a MasterData entry with category 'unit_of_measure'."
                    )

            updated_product = await crud.product.update(db, db_obj=product, obj_in=product_in)
            return updated_product

        @router.delete("/{product_id}", response_model=schemas.ProductInDB)
        async def delete_product(
            product_id: int,
            db: AsyncSession = Depends(deps.get_db),
            current_user: schemas.UserInDB = Depends(deps.get_current_active_user),
        ):
            """
            Deletes a product by its ID.
            """
            product = await crud.product.get(db, product_id)
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
            
            # Verify that the product belongs to a farm of the current user
            farm = await crud.farm.get(db, product.farm_id)
            if not farm or farm.created_by_user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permissions to delete this product."
                )

            deleted_product = await crud.product.remove(db, id=product_id)
            return deleted_product
        