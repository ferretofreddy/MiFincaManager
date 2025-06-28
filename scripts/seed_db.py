# scripts/seed_db.py
import asyncio
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Importa tus módulos, esquemas y crud
from app.db.session import async_sessionmaker 
from app.core.config import settings
from app import crud, models, schemas
from app.crud.exceptions import NotFoundError, AlreadyExistsError

# Datos de ejemplo
ADMIN_USER_EMAIL = settings.FIRST_SUPERUSER_EMAIL
ADMIN_USER_PASSWORD = settings.FIRST_SUPERUSER_PASSWORD
ADMIN_USER_FIRST_NAME = "Freddy"
ADMIN_USER_LAST_NAME = "Ferreto"

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
        user_in = schemas.UserCreate(
            email=ADMIN_USER_EMAIL,
            password=ADMIN_USER_PASSWORD, 
            first_name=ADMIN_USER_FIRST_NAME,
            last_name=ADMIN_USER_LAST_NAME,
            is_superuser=True,
            phone_number="60677676", 
            address="San Francisco", 
            country="Costa Rica", 
            city="San Vito" 
        )
        admin_user = await crud.user.create(db, obj_in=user_in) 
        if admin_user:
            print(f"Usuario administrador '{admin_user.email}' creado con éxito. ID: {admin_user.id}") 
        else:
            print(f"Error al crear el usuario administrador '{ADMIN_USER_EMAIL}'.")
            raise Exception("Failed to create admin user.")
    else:
        print(f"Usuario administrador '{admin_user.email}' ya existe. ID: {admin_user.id}") 
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

            # 1. Crear/Obtener Usuario Administrador
            admin_user = await create_or_get_admin_user(db)
            created_ids["users"]["admin"] = admin_user.id
            print(f"DEBUG: Admin User ID guardado: {admin_user.id}")

            # 2. Crear Módulos
            print("\nCreando módulos...")
            for module_data in MODULES_TO_CREATE:
                module_q = await db.execute(select(models.Module).filter(models.Module.name == module_data["name"]))
                module = module_q.scalars().first()
                if not module:
                    module_in = schemas.ModuleCreate(**module_data)
                    module = await crud.module.create(db, obj_in=module_in)
                    print(f"  Módulo '{module.name}' creado con ID: {module.id}.") 
                else:
                    print(f"  Módulo '{module.name}' ya existe. ID: {module.id}.") 
                created_ids["modules"][module.name] = module.id

            # 3. Crear Permisos y Asignar a Módulos
            print("\nCreando permisos y asignándolos a módulos...")
            for module_name, permissions_data in PERMISSIONS_TO_CREATE.items():
                module_id = created_ids["modules"].get(module_name)
                if not module_id:
                    print(f"  ADVERTENCIA: Módulo '{module_name}' no encontrado para permisos. Saltando.")
                    continue

                for perm_data in permissions_data:
                    permission_q = await db.execute(select(models.Permission).filter(models.Permission.name == perm_data["name"]))
                    permission = permission_q.scalars().first()
                    if not permission:
                        permission_in = schemas.PermissionCreate(module_id=module_id, **perm_data)
                        permission = await crud.permission.create(db, obj_in=permission_in)
                        print(f"    Permiso '{permission.name}' creado para módulo '{module_name}'. ID: {permission.id}") 
                    else:
                        print(f"    Permiso '{permission.name}' ya existe para módulo '{module_name}'. ID: {permission.id}") 
                    # No es estrictamente necesario guardar todos los IDs de permisos si no se usarán directamente
                    # created_ids["permissions"][permission.name] = permission.id 

            # 4. Crear Roles
            print("\nCreando roles...")
            # Obtener el ID del admin_user antes de intentar crear roles
            admin_user_id_for_roles = created_ids["users"]["admin"] 
            for role_data in ROLES_TO_CREATE:
                role_q = await db.execute(select(models.Role).filter(models.Role.name == role_data["name"]))
                role = role_q.scalars().first()
                if not role:
                    # === ¡CORRECCIÓN CRÍTICA AQUÍ! Pasar created_by_user_id ===
                    role_in = schemas.RoleCreate(created_by_user_id=admin_user_id_for_roles, **role_data)
                    role = await crud.role.create(db, obj_in=role_in)
                    print(f"  Rol '{role.name}' creado con ID: {role.id}.") 
                else:
                    print(f"  Rol '{role.name}' ya existe. ID: {role.id}.") 
                created_ids["roles"][role.name] = role.id
            
            print(f"DEBUG: Roles creados/existentes: {created_ids['roles']}") 


            # 5. Asignar Permisos a Roles (RolePermissions)
            print("\nAsignando permisos a roles...")
            admin_role_id = created_ids["roles"].get("Admin")
            if admin_role_id:
                admin_permissions_names = ADMIN_ROLE_PERMISSIONS.get("Admin", [])
                print(f"  DEBUG: Intentando asignar {len(admin_permissions_names)} permisos al rol 'Admin'.") 
                for perm_name in admin_permissions_names:
                    permission_q = await db.execute(select(models.Permission).filter(models.Permission.name == perm_name))
                    permission = permission_q.scalars().first()
                    if permission:
                        try:
                            await crud.role_permission.assign_permission_to_role(db, role_id=admin_role_id, permission_id=permission.id)
                            print(f"  Permiso '{perm_name}' asignado al rol 'Admin'.")
                        except AlreadyExistsError:
                            print(f"  Permiso '{perm_name}' ya asignado al rol 'Admin'.")
                        except Exception as e:
                            print(f"  Error al asignar permiso '{perm_name}' al rol 'Admin': {e}")
                    else:
                        print(f"  ADVERTENCIA: Permiso '{perm_name}' no encontrado. Saltando asignación.")
            else:
                print("  ADVERTENCIA: Rol 'Admin' no encontrado en created_ids. Saltando asignación de permisos.")


            standard_user_role_id = created_ids["roles"].get("Standard User")
            if standard_user_role_id:
                standard_permissions = [
                    "farm:read_all", "animal:read_all", "product:read_all",
                    "health_event:read_all", "reproductive_event:read_all",
                    "weighing:read_all", "feeding:read_all", "transaction:read_all",
                    "batch:read_all", "group:read_all", "master_data:read_all",
                    "config_param:read_all", "user:read", 
                ]
                print(f"  DEBUG: Intentando asignar {len(standard_permissions)} permisos al rol 'Standard User'.") 
                for perm_name in standard_permissions:
                    permission_q = await db.execute(select(models.Permission).filter(models.Permission.name == perm_name))
                    permission = permission_q.scalars().first()
                    if permission:
                        try:
                            await crud.role_permission.assign_permission_to_role(db, role_id=standard_user_role_id, permission_id=permission.id)
                            print(f"  Permiso '{perm_name}' asignado al rol 'Standard User'.")
                        except AlreadyExistsError:
                            print(f"  Permiso '{perm_name}' ya asignado al rol 'Standard User'.")
                        except Exception as e:
                            print(f"  Error al asignar permiso '{perm_name}' al rol 'Standard User': {e}")
                    else:
                        print(f"  ADVERTENCIA: Permiso '{perm_name}' no encontrado. Saltando asignación.")
            else:
                print("  ADVERTENCIA: Rol 'Standard User' no encontrado en created_ids. Saltando asignación de permisos.")


            # 6. Asignar Roles a Usuarios (UserRoles)
            print("\nAsignando roles a usuarios...")
            admin_user_id_for_user_roles = created_ids["users"].get("admin")
            if admin_user_id_for_user_roles and admin_role_id:
                try:
                    # Crear el objeto UserRoleCreate con los datos necesarios
                    user_role_in = schemas.UserRoleCreate(
                        user_id=admin_user_id_for_user_roles,
                        role_id=admin_role_id,
                        assigned_by_user_id=admin_user_id_for_user_roles
                    )
                    
                    # Usar el método create de CRUDUserRole
                    await crud.user_role.create(db, obj_in=user_role_in) # ¡Este es el cambio clave!
                    print(f"  Rol 'Admin' asignado al usuario {ADMIN_USER_EMAIL}.")
                except AlreadyExistsError:
                    print(f"  Rol 'Admin' ya asignado al usuario {ADMIN_USER_EMAIL}.")
                except Exception as e:
                    print(f"  Error al asignar rol 'Admin' al usuario {ADMIN_USER_EMAIL}: {e}")
            else:
                print("  ADVERTENCIA: Usuario administrador o rol 'Admin' no encontrado. Saltando asignación de rol.")

            print("\nSiembra de datos completada exitosamente.")

        except Exception as e:
            await db.rollback() 
            print(f"ERROR FATAL durante la siembra de datos: {e}")

if __name__ == "__main__":
    print("Ejecutando script de siembra. Esto puede tardar unos segundos...")
    asyncio.run(seed_db())
