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
                backupCount=5,
                encoding='utf-8'
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

def _is_writable_dir(path):
    try:
        test_path = os.path.join(path, ".write_test")
        with open(test_path, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(test_path)
        return True
    except Exception:
        return False

MASTER_DIR = None

def _resolve_data_dir():
    global MASTER_DIR
    env_dir = os.environ.get("ACTIVIDADES_DATA_DIR")
    if env_dir and os.path.isdir(env_dir):
        return env_dir
    candidate = DEFAULT_DATA_DIR
    if candidate.startswith("\\\\") or not _is_writable_dir(candidate):
        MASTER_DIR = candidate
        alt = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        candidate = os.path.join(alt, "ActividadesData")
        try:
            os.makedirs(candidate, exist_ok=True)
        except Exception:
            candidate = BASE_DIR
    return candidate

DATA_DIR = _resolve_data_dir()

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

def _copy_if_exists(src_dir, filename):
    try:
        src = os.path.join(src_dir, filename)
        dst = os.path.join(DATA_DIR, filename)
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
    except Exception:
        pass

def _ensure_templates():
    candidates = [BASE_DIR, os.path.dirname(BASE_DIR)]
    try:
        cwd = os.getcwd()
        candidates.extend([cwd, os.path.dirname(cwd)])
    except Exception:
        pass
    files = ["INFORME DE ACTIVIDADES - copia.xlsx", "InformeFinal.XLSX"]
    for fn in files:
        for cand in candidates:
            _copy_if_exists(cand, fn)

_ensure_templates()

def _dirs_search():
    dirs = []
    tmpl_env = os.environ.get("ACTIVIDADES_TEMPLATES_DIR")
    if tmpl_env and os.path.isdir(tmpl_env):
        dirs.append(tmpl_env)
    dirs.extend([DATA_DIR, os.path.dirname(DATA_DIR), BASE_DIR])
    try:
        cwd = os.getcwd()
        dirs.extend([cwd, os.path.dirname(cwd)])
    except Exception:
        pass
    seen = set()
    uniq = []
    for d in dirs:
        if d and d not in seen:
            uniq.append(d)
            seen.add(d)
    return uniq

DIRS_SEARCH = _dirs_search()

CONFIG_FILE = os.path.join(DATA_DIR, "config_actividades.json")
EXCEL_FILE = buscar_archivo("actividades.xlsx", DIRS_SEARCH)

def _resolve_db_file():
    import sqlite3
    def _db_score(p):
        try:
            cnt = 0
            with sqlite3.connect(p) as _c:
                _cur = _c.cursor()
                _cur.execute("SELECT COUNT(*) FROM registros")
                cnt = int(_cur.fetchone()[0])
        except Exception:
            cnt = 0
        try:
            mtime = os.path.getmtime(p)
            size = os.path.getsize(p)
        except Exception:
            mtime, size = 0, 0
        return (cnt, mtime, size)
    candidates = []
    for d in DIRS_SEARCH:
        for name in ("actividades.db", "database.db"):
            p = os.path.join(d, name)
            if os.path.exists(p):
                candidates.append((p,) + _db_score(p))
        sub = os.path.join(d, "dist", "actividades.db")
        if os.path.exists(sub):
            candidates.append((sub,) + _db_score(sub))
    # Siempre considerar el destino por defecto aunque no exista
    dst = os.path.join(DATA_DIR, "actividades.db")
    if not candidates:
        return dst
    # Elegir el de mayor cantidad de registros; empate → más reciente → mayor tamaño
    candidates.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)
    best = candidates[0][0]
    # Si el mejor no está en DATA_DIR, copiarlo allí
    try:
        if os.path.abspath(best) != os.path.abspath(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(best, dst)
            return dst
    except Exception:
        # Si falló la copia, usar el original
        return best
    return dst

DB_FILE = _resolve_db_file()

try:
    _legacy_db = os.path.join(DEFAULT_DATA_DIR, "actividades.db")
    if _legacy_db != DB_FILE and os.path.exists(_legacy_db) and not os.path.exists(DB_FILE):
        shutil.copy2(_legacy_db, DB_FILE)
except Exception:
    pass

def _resolve_usuarios_file():
    candidates = []
    for d in DIRS_SEARCH:
        p = os.path.join(d, "usuarios.json")
        if os.path.exists(p):
            candidates.append(p)
    if not candidates:
        return os.path.join(DATA_DIR, "usuarios.json")
    def score(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            users = data.get('usuarios', []) or []
            placeholders = {'usuario1','usuario2','usuario3'}
            real = [u for u in users if u and u.lower() not in placeholders]
            return (len(real), os.path.getmtime(path))
        except Exception:
            return (0, 0)
    best = max(candidates, key=score)
    # Copiar al DATA_DIR para estandarizar accesos futuros
    try:
        dst = os.path.join(DATA_DIR, "usuarios.json")
        if os.path.abspath(best) != os.path.abspath(dst):
            shutil.copy2(best, dst)
            return dst
    except Exception:
        pass
    return best

USERS_FILE = _resolve_usuarios_file()

def _ensure_data_file(filename):
    dst = os.path.join(DATA_DIR, filename)
    if not os.path.exists(dst):
        for cand in DIRS_SEARCH:
            src = os.path.join(cand, filename)
            if os.path.exists(src):
                try:
                    shutil.copy2(src, dst)
                except Exception:
                    pass
                break

_ensure_data_file("config_actividades.json")
_ensure_data_file("usuarios.json")
_ensure_data_file("actividades.xlsx")

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
    if os.path.exists(_repo_template) and not os.path.exists(os.path.join(DATA_DIR, "INFORME DE ACTIVIDADES - copia.xlsx")):
        shutil.copy2(_repo_template, os.path.join(DATA_DIR, "INFORME DE ACTIVIDADES - copia.xlsx"))
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

