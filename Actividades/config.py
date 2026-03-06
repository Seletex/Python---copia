"""
Módulo de configuración y logging para la aplicación.
Solo contiene constantes, valores por defecto y configuración de logging.
Las plantillas HTML están en templates.py
"""

import os
import sys
import json
import shutil
import logging
from logging.handlers import RotatingFileHandler

# =============================================================================
# CONSTANTES DE CONFIGURACIÓN
# =============================================================================

# =============================================================================
# CONSTANTES DE CONFIGURACIÓN
# =============================================================================

# =============================================================================
# CONFIGURACIÓN DE LOGGING (Inicializado temprano para traza de inicio)
# =============================================================================

def setup_logging():
    """Configura el sistema de logging para monitoreo de rendimiento"""
    # Encontrar BASE_DIR para los logs
    _base = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(_base, "logs")
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except:
            pass
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(
                os.path.join(log_dir, 'rendimiento.log') if os.path.exists(log_dir) else 'rendimiento.log',
                maxBytes=10*1024*1024,
                backupCount=5
            ),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# Inicializar logger de inmediato
try:
    logger = setup_logging()
    logger.info("--- INICIO DE CONFIGURACIÓN ---")
except Exception as e:
    print(f"Error configurando logging inicial: {e}")
    logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTES DE CONFIGURACIÓN
# =============================================================================

# Directorio base absoluto (donde está este archivo config.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if getattr(sys, 'frozen', False):
    DEFAULT_DATA_DIR = os.path.dirname(sys.executable)
else:
    DEFAULT_DATA_DIR = BASE_DIR

def buscar_archivo(nombre, directorios_prioridad):
    """Busca un archivo en varios directorios y devuelve la ruta absoluta del primero que exista."""
    for d in directorios_prioridad:
        if not d: continue
        ruta = os.path.normpath(os.path.join(d, nombre))
        if os.path.exists(ruta):
            logger.info(f"Archivo '{nombre}' encontrado en: {ruta}")
            return ruta
    
    # Si no se encuentra, devolver la ruta en el primer directorio por defecto
    ruta_defecto = os.path.normpath(os.path.join(directorios_prioridad[0], nombre))
    logger.warning(f"Archivo '{nombre}' NO ENCONTRADO. Usando ruta por defecto: {ruta_defecto}")
    return ruta_defecto

# Directorios donde buscar (Data dir, Parent dir, Base dir del script)
DIRS_SEARCH = [DEFAULT_DATA_DIR, os.path.dirname(DEFAULT_DATA_DIR), BASE_DIR]

CONFIG_FILE = os.path.join(DEFAULT_DATA_DIR, "config_actividades.json")
USERS_FILE = os.path.join(DEFAULT_DATA_DIR, "usuarios.json")
EXCEL_FILE = os.path.join(DEFAULT_DATA_DIR, "actividades.xlsx")
DB_FILE = os.path.join(DEFAULT_DATA_DIR, "actividades.db")

# Plantillas con búsqueda robusta
TEMPLATE_EXCEL = buscar_archivo("INFORME DE ACTIVIDADES - copia.xlsx", DIRS_SEARCH)
TEMPLATE_INFORME_FINAL = buscar_archivo("InformeFinal.XLSX", DIRS_SEARCH)

# =============================================================================
# MANTENIMIENTO DE PLANTILLAS Y OTROS
# =============================================================================

# Si en desarrollo existe una plantilla en el repo, copiarla a la carpeta
# de datos la primera vez si no existe allí.
_repo_template = os.path.join(BASE_DIR, "INFORME DE ACTIVIDADES - copia.xlsx")
try:
    if os.path.exists(_repo_template) and not os.path.exists(os.path.join(DEFAULT_DATA_DIR, "INFORME DE ACTIVIDADES - copia.xlsx")):
        shutil.copy2(_repo_template, os.path.join(DEFAULT_DATA_DIR, "INFORME DE ACTIVIDADES - copia.xlsx"))
except Exception:
    pass

DATABASE_URL = os.environ.get("DATABASE_URL") # URL de base de datos para Render (PostgreSQL)

# Columnas del Excel
COLUMNAS = [
    "ID", "USUARIO", "TIPO DE ACTIVIDAD", "FECHA", "DEPENDENCIA", "SOLICITANTE",
    "TIPO DE SOLICITUD", "MEDIO DE SOLICITUD", "DESCRIPCIÓN", "CUMPLIDO",
    "FECHA ATENCIÓN", "OBSERVACIONES"
]

# =============================================================================
# VALORES POR DEFECTO
# =============================================================================

ACTIVIDADES_DEFAULT = [
    "Brindar apoyo en la atención de requerimientos técnicos de primer nivel a los usuarios de la Administración Municipal, atendiendo incidentes relacionados con el funcionamiento de equipos de cómputo, impresoras, configuración de software y otros periféricos.",
    "Apoyar en el mantenimiento preventivo básico de equipos tecnológicos, realizando tareas como limpieza, revisión de cables, conectores y periféricos, con el objetivo de mantener en condiciones óptimas los recursos informáticos de la entidad.",
    "Colaborar en el control y actualización del inventario de activos tecnológicos, incluyendo equipos de cómputo, dispositivos de red, periféricos y demás recursos asignados a las dependencias, según los procedimientos establecidos por la oficina de sistemas.",
    "Apoyar en tareas logísticas relacionadas con la infraestructura tecnológica, tales como instalación, traslado o reubicación de equipos de cómputo, dispositivos de red y demás componentes tecnológicos, bajo supervisión del personal del área.",
    "Realizar seguimiento a solicitudes y requerimientos tecnológicos de los usuarios, documentando novedades, avances y necesidades adicionales, y comunicándolas oportunamente a los responsables correspondientes.",
    "Apoyar en la documentación técnica del área, incluyendo la organización y archivo de documentos, informes de soporte y demás registros, de acuerdo con las directrices internas y del Sistema de Gestión de Calidad.",
    "Colaborar en la implementación y seguimiento de medidas básicas de seguridad informática, tales como el monitoreo de alertas básicas, cierre adecuado de sesiones y cumplimiento de rutinas establecidas para el uso seguro de los recursos tecnológicos.",
    "Otro"
]

UBICACIONES_DEFAULT = [
    "ALCALDÍA", "ALMACEN MUNICIPAL", "ARCHIVO GENERAL", "BIBLIOTECAS", "CASA DE JUSTICIA",
    "CATASTRO", "CENTRO DÍA", "COMUNICACIONES", "CONCEJO MUNICIPAL", "CONTABILIDAD",
    "CONTRATACION", "CONTROL INTERNO", "DEPARTAMENTO GENERAL", "DEPARTAMENTO JURIDICO",
    "DESARROLLO COMUNITARIO", "DESARROLLO ECONOMICO", "EDUCACION Y CULTURA",
    "EJECUCIONES FISCALES", "GESTION HUMANA", "GESTIÓN PREDIAL", "GOBIERNO",
    "HACIENDA", "IMPUESTOS", "INFRAESTRUCTURA", "NOMINA", "OFICINA DE SISTEMAS",
    "PARQUE EDUCATIVO", "PERSONERÍA", "PLANEACIÓN", "PRESUPUESTO", "PROYECCIÓN SOCIAL",
    "SAIMYR", "SEGURIDAD Y SALUD EN EL TRABAJO", "SIGIN Y GINAT", "SISBEN", "TESORERIA"
]

TIPOS_SOLICITUD_DEFAULT = [
    "MANTENIMIENTO PREVENTIVO",
    "MANTENIMIENTO CORRECTIVE",
    "ASESORIA Y ASISTENCIA",
    "CAPACITACIÓN",
    "APOYO TECNOLÓGICO",
    "INSTALACIONES NUEVAS"
]

MEDIOS_SOLICITUD_DEFAULT = [
    "INTRANET",
    "LLAMADA TELEFONICA",
    "E-MAIL"
]

DEFAULT_USERS = {
    "usuarios": ["admin", "usuario1", "usuario2", "usuario3"],
    "configuraciones": {}
}

# =============================================================================
# CONFIGURACIÓN DE CACHE
# =============================================================================

_CACHE = {}
_CACHE_TIMEOUT = 30  # segundos

