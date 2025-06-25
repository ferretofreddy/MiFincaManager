# app/schemas/__init__.py
# Este archivo marca 'schemas' como un paquete.
# Aquí importaremos los esquemas de Pydantic para un acceso centralizado si se desea.

import pkgutil
import inspect
from pydantic import BaseModel

# Lista de módulos de esquemas que deben ser importados y reconstruidos.
# El orden de las importaciones aquí no es tan crítico como el de rebuild,
# pero es buena práctica listarlos.
# NO USAR "from .modulo import Clase1, Clase2" aquí, importaremos dinámicamente.

__all__ = [] # Para controlar lo que se exporta al importar 'schemas'

for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    # Ignorar __init__.py a sí mismo
    if module_name == '__init__':
        continue
    # Importar cada módulo de esquema
    module = loader.find_spec(module_name).loader.load_module(module_name)
    
    # Añadir los nombres de las clases (esquemas) al __all__ del paquete
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj.__name__ != 'BaseModel':
            globals()[name] = obj # Hace la clase accesible globalmente en __init__.py
            __all__.append(name)

# --- RECONSTRUCCIÓN DE MODELOS CENTRALIZADA Y DINÁMICA ---
# Este paso es CRÍTICO para Pydantic 2.x con ForwardRefs y dependencias cíclicas.
# Llama a model_rebuild() para todos los esquemas BaseModel importados.
for name in list(globals().keys()): # Iterar sobre una copia de las claves para evitar errores durante la modificación
    obj = globals()[name]
    if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj.__name__ != 'BaseModel':
        try:
            # print(f"Intentando reconstruir: {obj.__name__}") # Para depuración
            obj.model_rebuild()
        except Exception as e:
            # Esto captura errores durante la reconstrucción, lo que puede ayudar a identificar dependencias restantes
            print(f"Error al reconstruir el modelo {obj.__name__}: {e}")
            # Si el error persiste para un modelo específico, puede indicar un ForwardRef
            # mal formado o un ciclo muy complejo.

# Puedes eliminar las líneas de importación manuales anteriores si confías en la carga dinámica.
# Ejemplo de imports que se volverían redundantes (pero mantenlos por si el método dinámico falla)
# from .user import User, UserCreate, UserUpdate, UserReduced
# from .farm import Farm, FarmCreate, FarmUpdate, FarmReduced
# ... y así sucesivamente
