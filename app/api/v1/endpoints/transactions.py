# app/api/v1/endpoints/transactions.py
from fastapi import APIRouter, Depends, HTTPException, status, Response # Importa Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid

# --- Importaciones de módulos centrales ---
from app import schemas, models
from app.crud import transaction as crud_transaction # Importa la instancia CRUD para transaction
from app.crud import animal as crud_animal # Importa la instancia CRUD para animal
from app.crud import farm as crud_farm # Importa la instancia CRUD para farm
from app.crud import user as crud_user # Importa la instancia CRUD para user
from app.crud import master_data as crud_master_data # Importa la instancia CRUD para master_data


# --- Importaciones de dependencias y seguridad ---
from app.api import deps # Acceso a las dependencias de FastAPI

get_db = deps.get_db
get_current_active_user = deps.get_current_active_user


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
    responses={404: {"description": "Not found"}},
)

# --- Rutas de Transacciones ---

@router.post("/", response_model=schemas.Transaction, status_code=status.HTTP_201_CREATED)
async def create_new_transaction(
    transaction_in: schemas.TransactionCreate, # Renombrado
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Crea una nueva transacción.
    Se validan los IDs de animal, fincas y usuarios involucrados.
    """
    # 1. Validar animal_id
    animal_db = await crud_animal.get(db, id=transaction_in.animal_id)
    if not animal_db:
        raise HTTPException(status_code=400, detail=f"Animal with ID '{transaction_in.animal_id}' not found.")
    
    # 2. Validar from_owner_user_id (debe ser el usuario actual)
    # Asumiendo que el usuario actual es siempre el from_owner_user_id al crear.
    # Si from_owner_user_id puede ser diferente, la lógica de autorización debe cambiar.
    if str(transaction_in.from_owner_user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only create transactions as the 'from_owner_user'.")

    # 3. Validar from_farm_id (si se proporciona) y que pertenezca a from_owner_user
    if transaction_in.from_farm_id:
        from_farm_db = await crud_farm.get(db, id=transaction_in.from_farm_id)
        if not from_farm_db:
            raise HTTPException(status_code=400, detail=f"From Farm with ID '{transaction_in.from_farm_id}' not found.")
        if str(from_farm_db.owner_user_id) != str(current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="'From Farm' must belong to the current user.")

    # 4. Validar to_farm_id (si se proporciona)
    if transaction_in.to_farm_id:
        to_farm_db = await crud_farm.get(db, id=transaction_in.to_farm_id)
        if not to_farm_db:
            raise HTTPException(status_code=400, detail=f"To Farm with ID '{transaction_in.to_farm_id}' not found.")
        # TODO: Se podría añadir validación si to_farm también debe pertenecer al usuario o a un usuario con acceso.
        # Por ejemplo, si to_farm_id es una finca del usuario actual o de un usuario con acceso compartido.

    # 5. Validar to_owner_user_id (si se proporciona)
    if transaction_in.to_owner_user_id:
        to_owner_user_db = await crud_user.get(db, id=transaction_in.to_owner_user_id)
        if not to_owner_user_db:
            raise HTTPException(status_code=400, detail=f"To Owner User with ID '{transaction_in.to_owner_user_id}' not found.")

    # 6. Validar MasterData para transaction_type_id, unit_id, currency_id (si existen en el esquema)
    if hasattr(transaction_in, 'transaction_type_id') and transaction_in.transaction_type_id:
        transaction_type_md = await crud_master_data.get(db, id=transaction_in.transaction_type_id)
        if not transaction_type_md or transaction_type_md.category != 'transaction_type': # Ajusta la categoría si es diferente
            raise HTTPException(status_code=400, detail=f"Transaction type with ID '{transaction_in.transaction_type_id}' not found or invalid category.")

    if hasattr(transaction_in, 'unit_id') and transaction_in.unit_id:
        unit_md = await crud_master_data.get(db, id=transaction_in.unit_id)
        if not unit_md or unit_md.category != 'unit_of_measure': # Ajusta la categoría si es diferente
            raise HTTPException(status_code=400, detail=f"Unit with ID '{transaction_in.unit_id}' not found or invalid category.")

    if hasattr(transaction_in, 'currency_id') and transaction_in.currency_id:
        currency_md = await crud_master_data.get(db, id=transaction_in.currency_id)
        if not currency_md or currency_md.category != 'currency': # Ajusta la categoría si es diferente
            raise HTTPException(status_code=400, detail=f"Currency with ID '{transaction_in.currency_id}' not found or invalid category.")


    try:
        # Pasa recorded_by_user_id si tu CRUD de transaction lo espera para la auditoría
        db_transaction = await crud_transaction.create(db=db, obj_in=transaction_in, recorded_by_user_id=current_user.id)
        return db_transaction
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{transaction_id}", response_model=schemas.Transaction)
async def read_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtiene los detalles de una transacción específica.
    Solo accesible si el usuario es el 'from_owner' o el 'to_owner'.
    """
    db_transaction = await crud_transaction.get(db, id=transaction_id)
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Lógica de autorización: el usuario debe ser from_owner_user o to_owner_user
    if str(db_transaction.from_owner_user_id) != str(current_user.id) and \
       (db_transaction.to_owner_user_id is None or str(db_transaction.to_owner_user_id) != str(current_user.id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this transaction.")
    
    return db_transaction

@router.get("/", response_model=List[schemas.Transaction])
async def read_transactions(
    animal_id: Optional[uuid.UUID] = None, # Filtrar por animal
    from_owner_id: Optional[uuid.UUID] = None, # Filtrar por from_owner
    to_owner_id: Optional[uuid.UUID] = None, # Filtrar por to_owner
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtiene una lista de transacciones. Filtrado por animal o propietario.
    Solo muestra transacciones donde el usuario es el 'from_owner' o 'to_owner'.
    """
    # Lógica de autorización y filtrado delegada al CRUD para eficiencia
    # Asume un método crud_transaction.get_multi_by_user_and_filters
    transactions = await crud_transaction.get_multi_by_user_and_filters(
        db,
        current_user_id=current_user.id,
        animal_id=animal_id,
        from_owner_id=from_owner_id, # Pasa los filtros al CRUD
        to_owner_id=to_owner_id,     # Pasa los filtros al CRUD
        skip=skip,
        limit=limit
    )
    return transactions

@router.put("/{transaction_id}", response_model=schemas.Transaction)
async def update_existing_transaction(
    transaction_id: uuid.UUID,
    transaction_update: schemas.TransactionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Actualiza los detalles de una transacción específica.
    Solo el 'from_owner' original de la transacción puede actualizarla.
    """
    db_transaction = await crud_transaction.get(db, id=transaction_id)
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if str(db_transaction.from_owner_user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this transaction (only 'from_owner' can).")

    # Validar cualquier cambio en FKs
    if transaction_update.animal_id and transaction_update.animal_id != db_transaction.animal_id:
        animal_db = await crud_animal.get(db, id=transaction_update.animal_id)
        if not animal_db:
            raise HTTPException(status_code=400, detail=f"New animal with ID '{transaction_update.animal_id}' not found.")

    if transaction_update.from_farm_id and transaction_update.from_farm_id != db_transaction.from_farm_id:
        from_farm_db = await crud_farm.get(db, id=transaction_update.from_farm_id)
        if not from_farm_db:
            raise HTTPException(status_code=400, detail=f"New 'from_farm' with ID '{transaction_update.from_farm_id}' not found.")
        if str(from_farm_db.owner_user_id) != str(current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="New 'from_farm' must belong to the current user.")

    if transaction_update.to_farm_id and transaction_update.to_farm_id != db_transaction.to_farm_id:
        to_farm_db = await crud_farm.get(db, id=transaction_update.to_farm_id)
        if not to_farm_db:
            raise HTTPException(status_code=400, detail=f"New 'to_farm' with ID '{transaction_update.to_farm_id}' not found.")

    if transaction_update.from_owner_user_id and str(transaction_update.from_owner_user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change 'from_owner_user_id' to another user.")

    if transaction_update.to_owner_user_id and transaction_update.to_owner_user_id != db_transaction.to_owner_user_id:
        to_owner_user_db = await crud_user.get(db, id=transaction_update.to_owner_user_id)
        if not to_owner_user_db:
            raise HTTPException(status_code=400, detail=f"New 'to_owner_user' with ID '{transaction_update.to_owner_user_id}' not found.")

    # Validar MasterData si se actualizan (similar a la creación)
    if hasattr(transaction_update, 'transaction_type_id') and transaction_update.transaction_type_id is not None and transaction_update.transaction_type_id != db_transaction.transaction_type_id:
        transaction_type_md = await crud_master_data.get(db, id=transaction_update.transaction_type_id)
        if not transaction_type_md or transaction_type_md.category != 'transaction_type':
            raise HTTPException(status_code=400, detail=f"New transaction type with ID '{transaction_update.transaction_type_id}' not found or invalid category.")

    if hasattr(transaction_update, 'unit_id') and transaction_update.unit_id is not None and transaction_update.unit_id != db_transaction.unit_id:
        unit_md = await crud_master_data.get(db, id=transaction_update.unit_id)
        if not unit_md or unit_md.category != 'unit_of_measure':
            raise HTTPException(status_code=400, detail=f"New unit with ID '{transaction_update.unit_id}' not found or invalid category.")

    if hasattr(transaction_update, 'currency_id') and transaction_update.currency_id is not None and transaction_update.currency_id != db_transaction.currency_id:
        currency_md = await crud_master_data.get(db, id=transaction_update.currency_id)
        if not currency_md or currency_md.category != 'currency':
            raise HTTPException(status_code=400, detail=f"New currency with ID '{transaction_update.currency_id}' not found or invalid category.")


    try:
        updated_transaction = await crud_transaction.update(db, db_obj=db_transaction, obj_in=transaction_update)
        if updated_transaction is None:
            raise HTTPException(status_code=500, detail="Failed to update transaction unexpectedly.") 
        return updated_transaction
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Elimina una transacción específica.
    Solo el 'from_owner' original de la transacción puede eliminarla.
    """
    db_transaction = await crud_transaction.get(db, id=transaction_id)
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if str(db_transaction.from_owner_user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this transaction (only 'from_owner' can).")
    
    deleted_transaction = await crud_transaction.remove(db, id=transaction_id)
    if not deleted_transaction:
        raise HTTPException(status_code=500, detail="Failed to delete transaction unexpectedly.")
    return Response(status_code=status.HTTP_204_NO_CONTENT) # Retorno correcto para 204

