# app/enums/__init__.py
# Se importan todos los Enum directamente
import enum

# Sexo de los animales
class SexEnumPython(str, enum.Enum):
    MACHO = "Macho"
    HEMBRA = "Hembra"
    CASTRADO = "Castrado"

# Estado actual de los animales
class AnimalStatusEnumPython(str, enum.Enum):
    ACTIVO = "Activo"
    VENDIDO = "Vendido"
    MUERTO = "Muerto"
    EN_TRATAMIENTO = "En Tratamiento"
    CUARENTENA = "Cuarentena"
    REFORMADO = "Reformado" # Retirado de produccion/reproduccion

# Origen del animal
class AnimalOriginEnumPython(str, enum.Enum):
    NACIDO_EN_FINCA = "Nacido en Finca"
    COMPRADO = "Comprado"
    TRANSFERIDO = "Transferido" # De otra finca del mismo dueño

# Tipos de eventos de salud
class HealthEventTypeEnumPython(str, enum.Enum):
    VACUNACION = "Vacunacion" # Asegúrate de que el JSON use "Vacunacion" tal cual
    DESPARACITACION = "Desparacitacion"
    REVISION_MEDICA = "Revision_Medica"
    TRATAMIENTO_ENFERMEDAD = "Tratamiento_Enfermedad"
    CIRUGIA = "Cirugia"
    MUERTE = "Muerte"
    OTRO = "Otro"

# Tipos de eventos reproductivos
class ReproductiveEventTypeEnumPython(str, enum.Enum):
    MONTA = "Monta"
    INSEMINACION_ARTIFICIAL = "Inseminacion_Artificial"
    DIAGNOSTICO_GESTACION = "Diagnostico_Gestacion"
    PARTO = "Parto"
    ABORTO = "Aborto"
    DESTETE = "Destete"
    EVALUACION_REPRODUCTIVA = "Evaluacion_Reproductiva"

# Resultado del diagnostico de gestacion
class GestationDiagnosisResultEnumPython(str, enum.Enum):
    PRENADA = "Preñada"
    VACIA = "Vacia"
    NO_APLICA = "No Aplica" # Para eventos que no son diagnostico de gestacion

# Tipos de transaccion/movimiento de animales
class TransactionTypeEnumPython(str, enum.Enum):
    COMPRA = "Compra"
    VENTA = "Venta"
    TRASLADO = "Traslado" # Entre fincas del mismo dueño
    NACIMIENTO = "Nacimiento" # Aunque se maneja mas por OffspringBorn
    MUERTE = "Muerte"
    ROBO = "Robo"
    PERDIDA = "Perdida"

# Tipos de datos para parametros de configuracion
class ParamDataTypeEnumPython(str, enum.Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    JSON = "json"

