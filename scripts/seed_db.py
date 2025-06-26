# scripts/seed_db.py
import asyncio
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Importa tus módulos, esquemas y crud
from app.db.session import async_sessionmaker 
from app.core.config import settings
# YA NO NECESITAMOS get_password_hash AQUÍ para el UserCreate
# from app.core.security import get_password_hash 
from app import crud, models, schemas
from app.crud.exceptions import NotFoundError, AlreadyExistsError

# Datos de ejemplo
# Puedes cambiar la contraseña del usuario administrador
ADMIN_USER_EMAIL = settings.FIRST_SUPERUSER_EMAIL
ADMIN_USER_PASSWORD = settings.FIRST_SUPERUSER_PASSWORD
ADMIN_USER_FIRST_NAME = "Super"
ADMIN_USER_LAST_NAME = "Admin"

MODULES_TO_CREATE = [
    {"name": "Farm", "description": "Gestión de fincas"},
    {"name": "Animal", "description": "Gestión de animales"},
    {"name": "Product", "description": "Gestión de productos e inventario"},
    {"name": "Health", "description": "Gestión de eventos de salud animal"},
    {"name": "Reproduction", "description": "Gestión de eventos reproductivos"},
    {"name": "Weighing", "description": "Registro de pesajes de animales"},
    {"name": "Feeding", "description": "Registro de alimentación"},
    {"name": "Transaction", "description": "Registro de transacciones (compra/venta)"},
    {"name": "Batch", "description": "Gestión de lotes de animales/productos"},
    {"name": "Group", "description": "Gestión de grupos de animales"},
    {"name": "MasterData", "description": "Gestión de datos maestros (tipos, unidades, etc.)"},
    {"name": "Security", "description": "Gestión de usuarios, roles y permisos"},
    {"name": "Configuration", "description": "Gestión de parámetros de configuración"},
]

PERMISSIONS_TO_CREATE = {
    "Farm": [
        {"name": "farm:create", "description": "Permite crear nuevas fincas."},
        {"name": "farm:read", "description": "Permite leer información de una finca específica."},
        {"name": "farm:read_all", "description": "Permite listar todas las fincas en el sistema."},
        {"name": "farm:update", "description": "Permite actualizar información de una finca."},
        {"name": "farm:delete", "description": "Permite eliminar una finca."},
    ],
    "Security": [
        {"name": "user:create", "description": "Permite crear nuevos usuarios."},
        {"name": "user:read", "description": "Permite leer información de un usuario."},
        {"name": "user:read_all", "description": "Permite listar todos los usuarios."},
        {"name": "user:update", "description": "Permite actualizar un usuario."},
        {"name": "user:delete", "description": "Permite eliminar un usuario."},
        {"name": "role:create", "description": "Permite crear nuevos roles."},
        {"name": "role:read", "description": "Permite leer información de un rol."},
        {"name": "role:read_all", "description": "Permite listar todos los roles."},
        {"name": "role:update", "description": "Permite actualizar un rol."},
        {"name": "role:delete", "description": "Permite eliminar un rol."},
        {"name": "permission:read_all", "description": "Permite listar todos los permisos."},
        {"name": "role_permission:assign", "description": "Permite asignar permisos a roles."},
        {"name": "user_role:assign", "description": "Permite asignar roles a usuarios."},
        {"name": "user_farm_access:assign", "description": "Permite asignar acceso a fincas a usuarios."},
    ],
    "MasterData": [
        {"name": "master_data:create", "description": "Permite crear nuevas entradas de datos maestros."},
        {"name": "master_data:read", "description": "Permite leer información de una entrada de datos maestros."},
        {"name": "master_data:read_all", "description": "Permite listar todas las entradas de datos maestros."},
        {"name": "master_data:update", "description": "Permite actualizar una entrada de datos maestros."},
        {"name": "master_data:delete", "description": "Permite eliminar una entrada de datos maestros."},
    ],
    "Configuration": [
        {"name": "config_param:read_all", "description": "Permite leer todos los parámetros de configuración."},
        {"name": "config_param:update", "description": "Permite actualizar parámetros de configuración."},
    ],
    "Animal": [
        {"name": "animal:create", "description": "Permite crear nuevos animales."},
        {"name": "animal:read", "description": "Permite leer información de un animal."},
        {"name": "animal:read_all", "description": "Permite listar todos los animales."},
        {"name": "animal:update", "description": "Permite actualizar un animal."},
        {"name": "animal:delete", "description": "Permite eliminar un animal."},
    ],
    "Product": [
        {"name": "product:create", "description": "Permite crear nuevos productos."},
        {"name": "product:read", "description": "Permite leer información de un producto."},
        {"name": "product:read_all", "description": "Permite listar todos los productos."},
        {"name": "product:update", "description": "Permite actualizar un producto."},
        {"name": "product:delete", "description": "Permite eliminar un producto."},
    ],
    "Health": [
        {"name": "health_event:create", "description": "Permite crear nuevos eventos de salud."},
        {"name": "health_event:read", "description": "Permite leer información de un evento de salud."},
        {"name": "health_event:read_all", "description": "Permite listar todos los eventos de salud."},
        {"name": "health_event:update", "description": "Permite actualizar un evento de salud."},
        {"name": "health_event:delete", "description": "Permite eliminar un evento de salud."},
    ],
    "Reproduction": [
        {"name": "reproductive_event:create", "description": "Permite crear nuevos eventos reproductivos."},
        {"name": "reproductive_event:read", "description": "Permite leer información de un evento reproductivo."},
        {"name": "reproductive_event:read_all", "description": "Permite listar todos los eventos reproductivos."},
        {"name": "reproductive_event:update", "description": "Permite actualizar un evento reproductivo."},
        {"name": "reproductive_event:delete", "description": "Permite eliminar un evento reproductivo."},
    ],
    "Weighing": [
        {"name": "weighing:create", "description": "Permite crear nuevos registros de pesaje."},
        {"name": "weighing:read", "description": "Permite leer información de un registro de pesaje."},
        {"name": "weighing:read_all", "description": "Permite listar todos los registros de pesaje."},
        {"name": "weighing:update", "description": "Permite actualizar un registro de pesaje."},
        {"name": "weighing:delete", "description": "Permite eliminar un registro de pesaje."},
    ],
    "Feeding": [
        {"name": "feeding:create", "description": "Permite crear nuevos registros de alimentación."},
        {"name": "feeding:read", "description": "Permite leer información de un registro de alimentación."},
        {"name": "feeding:read_all", "description": "Permite listar todos los registros de alimentación."},
        {"name": "feeding:update", "description": "Permite actualizar un registro de alimentación."},
        {"name": "feeding:delete", "description": "Permite eliminar un registro de alimentación."},
    ],
    "Transaction": [
        {"name": "transaction:create", "description": "Permite crear nuevas transacciones."},
        {"name": "transaction:read", "description": "Permite leer información de una transacción."},
        {"name": "transaction:read_all", "description": "Permite listar todas las transacciones."},
        {"name": "transaction:update", "description": "Permite actualizar una transacción."},
        {"name": "transaction:delete", "description": "Permite eliminar una transacción."},
    ],
    "Batch": [
        {"name": "batch:create", "description": "Permite crear nuevos lotes."},
        {"name": "batch:read", "description": "Permite leer información de un lote."},
        {"name": "batch:read_all", "description": "Permite listar todos los lotes."},
        {"name": "batch:update", "description": "Permite actualizar un lote."},
        {"name": "batch:delete", "description": "Permite eliminar un lote."},
    ],
    "Group": [
        {"name": "group:create", "description": "Permite crear nuevos grupos de animales."},
        {"name": "group:read", "description": "Permite leer información de un grupo de animales."},
        {"name": "group:read_all", "description": "Permite listar todos los grupos de animales."},
        {"name": "group:update", "description": "Permite actualizar un grupo de animales."},
        {"name": "group:delete", "description": "Permite eliminar un grupo de animales."},
    ],
}

ROLES_TO_CREATE = [
    {"name": "Admin", "description": "Rol con acceso completo a todas las funcionalidades."},
    {"name": "Standard User", "description": "Rol con acceso estándar a las funcionalidades básicas."},
]

ADMIN_ROLE_PERMISSIONS = {
    "Admin": [
        p["name"] for module_perms in PERMISSIONS_TO_CREATE.values() for p in module_perms
    ]
}

async def create_or_get_admin_user(db: AsyncSession) -> models.User:
    """
    Crea o recupera el usuario administrador.
    """
    admin_user_q = await db.execute(
        select(models.User).filter(models.User.email == ADMIN_USER_EMAIL)
    )
    admin_user = admin_user_q.scalars().first()

    if not admin_user:
        print("Creando nuevo usuario administrador.")
        # === ¡CORRECCIÓN CLAVE AQUÍ! ===
        # Pasamos el password en texto plano, el CRUD se encargará de hashearlo
        user_in = schemas.UserCreate(
            email=ADMIN_USER_EMAIL,
            password=ADMIN_USER_PASSWORD, # <--- ¡CAMBIADO! Pasar el password en texto plano
            first_name=ADMIN_USER_FIRST_NAME,
            last_name=ADMIN_USER_LAST_NAME,
            is_superuser=True,
            phone_number="123456789", 
            address="Calle Principal 123", 
            country="Costa Rica", 
            city="San Jose" 
        )
        admin_user = await crud.user.create(db, obj_in=user_in) 
        if admin_user:
            print(f"Usuario administrador '{admin_user.email}' creado con éxito.")
        else:
            print(f"Error al crear el usuario administrador '{ADMIN_USER_EMAIL}'.")
            raise Exception("Failed to create admin user.")
    else:
        print(f"Usuario administrador '{admin_user.email}' ya existe.")
    return admin_user

async def seed_db():
    """
    Siembra la base de datos con datos iniciales.
    """
    session_instance = async_sessionmaker() 
    async with session_instance as db: 
        try:
            print("Iniciando la siembra de datos...")
            created_ids = {
                "users": {},
                "modules": {},
                "permissions": {},
                "roles": {},
                "master_data_categories": { 
                    "species": {}, "breed": {}, "transaction_type": {},
                    "unit_of_measure": {}, "currency": {}, "entity_type": {},
                    "batch_type": {}, "group_purpose": {}, "product_type": {},
                    "health_event_type": {}
                }
            }

            admin_user = await create_or_get_admin_user(db)
            created_ids["users"]["admin"] = admin_user.id

            # ... el resto del código de siembra ...

            print("\nSiembra de datos completada exitosamente.")

        except Exception as e:
            await db.rollback() 
            print(f"ERROR FATAL durante la siembra de datos: {e}")

if __name__ == "__main__":
    print("Ejecutando script de siembra. Esto puede tardar unos segundos...")
    asyncio.run(seed_db())
