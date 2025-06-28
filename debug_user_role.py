# debug_user_role.py
import asyncio
import uuid
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_sessionmaker 
from app.crud import user_role as crud_user_role
from app.crud import user as crud_user 
from app.crud import role as crud_role 
from app.crud.exceptions import AlreadyExistsError, NotFoundError, CRUDException
from app.models.user_role import UserRole 
from app.schemas.user_role import UserRoleCreate 

async def debug_assignment():
    session_instance = async_sessionmaker() 
    async with session_instance as db:
        print("\n--- INICIO DEL DIAGNÓSTICO DE ASIGNACIÓN DE ROL ---")

        # === ¡ACTUALIZAR ESTOS IDS CON LOS DE TUS CAPTURAS/DB ACTUAL! ===
        # Reemplaza con los IDs EXACTOS de tus capturas
        USER_ID_TO_ASSIGN = uuid.UUID("683618ab-83bb-4be7-bcd7-9211f0bc04ba") # ID de ferretofreddy@hotmail.com
        ROLE_ID_TO_ASSIGN = uuid.UUID("56ba17f0-39d1-46b3-aa1e-79cfb63994b5") # ID de Standard User
        ASSIGNED_BY_USER_ID = uuid.UUID("e685ed4a-511c-4dbd-9355-9917853ef433") # ID de ferretofreddy@gmail.com (Super Admin)

        # 1. Verificar existencia de usuario y rol (a nivel de DB)
        db_user = await crud_user.get(db, id=USER_ID_TO_ASSIGN)
        db_role = await crud_role.get(db, id=ROLE_ID_TO_ASSIGN)
        db_assigner = await crud_user.get(db, id=ASSIGNED_BY_USER_ID)

        print(f"Usuario '{db_user.email if db_user else 'N/A'}' ({USER_ID_TO_ASSIGN}) existe: {'Sí' if db_user else 'No'}")
        print(f"Rol '{db_role.name if db_role else 'N/A'}' ({ROLE_ID_TO_ASSIGN}) existe: {'Sí' if db_role else 'No'}")
        print(f"Usuario que asigna '{db_assigner.email if db_assigner else 'N/A'}' ({ASSIGNED_BY_USER_ID}) existe: {'Sí' if db_assigner else 'No'}")

        if not db_user or not db_role or not db_assigner:
            print("ERROR: Faltan usuario, rol o usuario que asigna en la base de datos. Asegúrate de que seed_db se ejecutó correctamente y los IDs son válidos.")
            return

        # 2. Verificar si la relación ya existe ANTES de intentar crearla (consulta directa a la DB)
        print("\n--- Verificación Directa de la Relación en DB ---")
        direct_check_result = await db.execute(
            select(UserRole)
            .filter(UserRole.user_id == USER_ID_TO_ASSIGN, UserRole.role_id == ROLE_ID_TO_ASSIGN)
        )
        direct_existing = direct_check_result.scalar_one_or_none()
        print(f"Relación (user_id={USER_ID_TO_ASSIGN}, role_id={ROLE_ID_TO_ASSIGN}) ya existe en DB?: {'Sí' if direct_existing else 'No'}")
        if direct_existing:
            print(f"DETALLE: La asociación existente es: {direct_existing.id} (user_id={direct_existing.user_id}, role_id={direct_existing.role_id}, assigned_by_user_id={direct_existing.assigned_by_user_id})")
            print("Puedes borrarla directamente de la DB si estás seguro de que es un registro 'fantasma' o si quieres reintentar.")
            print("Ejemplo SQL para borrar: DELETE FROM user_roles WHERE user_id = '{}' AND role_id = '{}';".format(USER_ID_TO_ASSIGN, ROLE_ID_TO_ASSIGN))

        # 3. Intentar crear la relación usando el método CRUD
        print("\n--- Intentando crear la relación via CRUD ---")
        user_role_in = UserRoleCreate(
            user_id=USER_ID_TO_ASSIGN,
            role_id=ROLE_ID_TO_ASSIGN,
            assigned_by_user_id=ASSIGNED_BY_USER_ID
        )

        try:
            new_association = await crud_user_role.create(db, obj_in=user_role_in)
            print(f"¡Asignación exitosa! Nueva asociación ID: {new_association.id}")
        except AlreadyExistsError as e:
            print(f"Error: La asociación ya existe (CRUD lanzó AlreadyExistsError): {e}")
        except NotFoundError as e:
            print(f"Error: Elemento no encontrado durante la asignación (CRUD lanzó NotFoundError): {e}")
        except CRUDException as e:
            print(f"Error general del CRUD durante asignación (CRUD lanzó CRUDException): {e}")
        except Exception as e:
            print(f"Error inesperado durante asignación: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc() 

        print("\n--- FIN DEL DIAGNÓSTICO ---")

if __name__ == "__main__":
    asyncio.run(debug_assignment())
