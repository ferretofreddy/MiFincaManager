# routers/transactions.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid

from database import get_db
import schemas
import crud
from dependencies import get_current_user 
import models # Para los modelos ORM

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
    responses={404: {"description": "Not found"}},
)

# --- Rutas de Transacciones ---

@router.post("/", response_model=schemas.Transaction, status_code=status.HTTP_201_CREATED)
async def create_new_transaction(
    transaction: schemas.TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Crea una nueva transacción.
    Se validan los IDs de animal, fincas y usuarios involucrados.
    """
    # Validar que el animal existe y es propiedad del usuario o accesible por su finca (si es from_owner)
    animal_db = await crud.get_animal(db, transaction.animal_id)
    if not animal_db:
        raise HTTPException(status_code=400, detail=f"Animal with ID '{transaction.animal_id}' not found.")
    
    # Validar from_owner_user_id (debe ser el usuario actual)
    if str(transaction.from_owner_user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only create transactions as the 'from_owner_user'.")

    # Validar from_farm_id (si se proporciona) y que pertenezca a from_owner_user
    if transaction.from_farm_id:
        from_farm_db = await crud.get_farm(db, transaction.from_farm_id)
        if not from_farm_db:
            raise HTTPException(status_code=400, detail=f"From Farm with ID '{transaction.from_farm_id}' not found.")
        if str(from_farm_db.owner_user_id) != str(current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="'From Farm' must belong to the current user.")

    # Validar to_farm_id (si se proporciona)
    if transaction.to_farm_id:
        to_farm_db = await crud.get_farm(db, transaction.to_farm_id)
        if not to_farm_db:
            raise HTTPException(status_code=400, detail=f"To Farm with ID '{transaction.to_farm_id}' not found.")
        # TODO: Se podría añadir validación si to_farm también debe pertenecer al usuario o a un usuario con acceso.

    # Validar to_owner_user_id (si se proporciona)
    if transaction.to_owner_user_id:
        to_owner_user_db = await crud.get_user(db, transaction.to_owner_user_id)
        if not to_owner_user_db:
            raise HTTPException(status_code=400, detail=f"To Owner User with ID '{transaction.to_owner_user_id}' not found.")

    try:
        db_transaction = await crud.create_transaction(db=db, transaction=transaction)
        return db_transaction
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{transaction_id}", response_model=schemas.Transaction)
async def read_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene los detalles de una transacción específica.
    Solo accesible si el usuario es el 'from_owner' o el 'to_owner'.
    """
    db_transaction = await crud.get_transaction(db, transaction_id=transaction_id)
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
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene una lista de transacciones. Filtrado por animal o propietario.
    Solo muestra transacciones donde el usuario es el 'from_owner' o 'to_owner'.
    """
    # Siempre filtrar por transacciones donde el usuario es parte, a menos que sea un admin
    # TODO: Implementar lógica de administrador si se necesita ver todas las transacciones.

    # Obtener todas las transacciones donde el current_user es from_owner o to_owner
    all_transactions = await crud.get_transactions(db, skip=0, limit=None)
    
    user_transactions = [
        t for t in all_transactions 
        if str(t.from_owner_user_id) == str(current_user.id) or 
           (t.to_owner_user_id and str(t.to_owner_user_id) == str(current_user.id))
    ]

    # Aplicar filtros adicionales
    if animal_id:
        user_transactions = [t for t in user_transactions if t.animal_id == animal_id]
    if from_owner_id:
        if str(from_owner_id) != str(current_user.id): # Solo se puede filtrar por el propio ID como from_owner
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only filter by your own 'from_owner' ID.")
        user_transactions = [t for t in user_transactions if str(t.from_owner_user_id) == str(from_owner_id)]
    if to_owner_id:
        if str(to_owner_id) != str(current_user.id): # Solo se puede filtrar por el propio ID como to_owner
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only filter by your own 'to_owner' ID.")
        user_transactions = [t for t in user_transactions if t.to_owner_user_id and str(t.to_owner_user_id) == str(to_owner_id)]

    # Aplicar paginación
    return user_transactions[skip : skip + limit]

@router.put("/{transaction_id}", response_model=schemas.Transaction)
async def update_existing_transaction(
    transaction_id: uuid.UUID,
    transaction_update: schemas.TransactionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Actualiza los detalles de una transacción específica.
    Solo el 'from_owner' original de la transacción puede actualizarla.
    """
    db_transaction = await crud.get_transaction(db, transaction_id=transaction_id)
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if str(db_transaction.from_owner_user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this transaction (only 'from_owner' can).")

    # Validar cualquier cambio en FKs
    if transaction_update.animal_id and transaction_update.animal_id != db_transaction.animal_id:
        animal_db = await crud.get_animal(db, transaction_update.animal_id)
        if not animal_db:
            raise HTTPException(status_code=400, detail=f"New animal with ID '{transaction_update.animal_id}' not found.")

    if transaction_update.from_farm_id and transaction_update.from_farm_id != db_transaction.from_farm_id:
        from_farm_db = await crud.get_farm(db, transaction_update.from_farm_id)
        if not from_farm_db:
            raise HTTPException(status_code=400, detail=f"New 'from_farm' with ID '{transaction_update.from_farm_id}' not found.")
        if str(from_farm_db.owner_user_id) != str(current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="New 'from_farm' must belong to the current user.")

    if transaction_update.to_farm_id and transaction_update.to_farm_id != db_transaction.to_farm_id:
        to_farm_db = await crud.get_farm(db, transaction_update.to_farm_id)
        if not to_farm_db:
            raise HTTPException(status_code=400, detail=f"New 'to_farm' with ID '{transaction_update.to_farm_id}' not found.")

    if transaction_update.from_owner_user_id and str(transaction_update.from_owner_user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change 'from_owner_user_id' to another user.")

    if transaction_update.to_owner_user_id and transaction_update.to_owner_user_id != db_transaction.to_owner_user_id:
        to_owner_user_db = await crud.get_user(db, transaction_update.to_owner_user_id)
        if not to_owner_user_db:
            raise HTTPException(status_code=400, detail=f"New 'to_owner_user' with ID '{transaction_update.to_owner_user_id}' not found.")


    try:
        updated_transaction = await crud.update_transaction(db, transaction_id, transaction_update)
        if updated_transaction is None:
            raise HTTPException(status_code=500, detail="Failed to update transaction unexpectedly.") 
        return updated_transaction
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Elimina una transacción específica.
    Solo el 'from_owner' original de la transacción puede eliminarla.
    """
    db_transaction = await crud.get_transaction(db, transaction_id=transaction_id)
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if str(db_transaction.from_owner_user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this transaction (only 'from_owner' can).")
    
    try:
        deleted = await crud.delete_transaction(db, transaction_id)
        if not deleted:
            raise HTTPException(status_code=500, detail="Failed to delete transaction unexpectedly.")
        return {"message": "Transaction deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
