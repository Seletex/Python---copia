"""
Módulo de configuración y logging para la aplicación.
Solo contiene constantes, valores por defecto y configuración de logging.
Las plantillas HTML están en templates.py
"""

import os
import json
import logging
from logging.handlers import RotatingFileHandler

# =============================================================================
# CONSTANTES DE CONFIGURACIÓN
# =============================================================================

CONFIG_FILE = "config_actividades.json"
USERS_FILE = "usuarios.json"
EXCEL_FILE = "actividades.xlsx"
TEMPLATE_EXCEL = r"c:\Users\apoyosistemas\Documents\Python - copia\INFORME DE ACTIVIDADES - copia.xlsx"

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
    "MANTENIMIENTO CORRECTIVO",
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

# =============================================================================
# CONFIGURACIÓN DE LOGGING
# =============================================================================

def setup_logging():
    """Configura el sistema de logging para monitoreo de rendimiento"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(
                os.path.join(log_dir, 'rendimiento.log'),
                maxBytes=10*1024*1024,
                backupCount=5
            ),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

# Inicializar logger
try:
    logger = setup_logging()
    logger.info("Sistema de logging inicializado correctamente")
except Exception as e:
    print(f"Error configurando logging: {e}")
    logger = logging.getLogger(__name__)
