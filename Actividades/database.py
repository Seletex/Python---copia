
"""
Módulo de base de datos SQLITE: reemplaza la versión basada en archivos.
Implementa la misma interfaz que database.py pero usando SQLite.
"""

import os
import json
import sqlite3
import time
import random
import pandas as pd
from config import (
    EXCEL_FILE, USERS_FILE, CONFIG_FILE, DB_FILE, DATABASE_URL, COLUMNAS, 
    ACTIVIDADES_DEFAULT, UBICACIONES_DEFAULT, TIPOS_SOLICITUD_DEFAULT, MEDIOS_SOLICITUD_DEFAULT,
    logger, DIRS_SEARCH, MASTER_DIR
)
from utils import cache_decorator, medir_tiempo, clear_cache
from contextlib import contextmanager

# Intentar importar psycopg2 para PostgreSQL (Render)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None

# DB_NAME eliminado, usamos DB_FILE de config

def retry_operation(max_retries=5, base_delay=0.5):
    """Decorador para reintentar operaciones de BD en caso de bloqueo o I/O error"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (sqlite3.OperationalError, sqlite3.DatabaseError, OSError, PermissionError) as e:
                    last_exception = e
                    sleep_time = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                    logger.warning(f"[WARNING] Reintento {attempt + 1}/{max_retries} en {func.__name__} por: {e}. Esperando {sleep_time:.2f}s")
                    time.sleep(sleep_time)
            logger.error(f"[ERROR] Fallo crítico en {func.__name__} después de {max_retries} intentos.")
            raise last_exception
        return wrapper
    return decorator

def get_db_connection():
    """Obtiene conexión a BD (PostgreSQL si hay URL, sino SQLite)"""
    if DATABASE_URL and psycopg2:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            return conn
        except Exception as e:
            logger.error(f"Error conectando a Postgres: {e}")
            # Fallback a SQLite si falla Postgres (opcional)
    
    # Resiliencia para SQLite en red
    conn = None
    try:
        # Timeout aumentado considerablemente para redes lentas
        conn = sqlite3.connect(DB_FILE, timeout=30)
        conn.row_factory = sqlite3.Row
        # Habilitar Write-Ahead Logging (WAL) mejora concurrencia, 
        # pero NORMAL es más seguro en red inestable que WAL puro a veces
        conn.execute("PRAGMA journal_mode=TRUNCATE") # TRUNCATE suele ser más estable en red que WAL si hay desconexiones
        conn.execute("PRAGMA synchronous=FULL")      # Máxima seguridad de datos
    except Exception as e:
        logger.error(f"Error fatal conectando a SQLite: {e}")
        raise e
        
    return conn

def get_cursor(conn):
    """Devuelve un cursor tipo diccionario compatible entre ambos motores"""
    if DATABASE_URL and psycopg2 and isinstance(conn, psycopg2.extensions.connection):
        return conn.cursor(cursor_factory=RealDictCursor)
    return conn.cursor()

@contextmanager
def db_session():
    """Context manager para asegurar que las conexiones se cierren siempre"""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def fix_query(query):
    """Adapta la sintaxis de la consulta de SQLite (?) a Postgres (%s)"""
    if DATABASE_URL and psycopg2:
        return query.replace('?', '%s').replace('INSERT OR IGNORE', 'INSERT').replace('AUTOINCREMENT', '')
    return query

@retry_operation(max_retries=5, base_delay=1.0)
def inicializar_tablas():
    """Crea todas las tablas necesarias si no existen (SQLite y Postgres)"""
    try:
        conn = get_db_connection()
        cursor = get_cursor(conn)
        
        # 1. Crear tabla de usuarios
        cursor.execute(fix_query("CREATE TABLE IF NOT EXISTS usuarios (username TEXT PRIMARY KEY)"))
        
        # 2. Crear tabla de actividades personales
        cursor.execute(fix_query("CREATE TABLE IF NOT EXISTS actividades_personales (username TEXT, actividad TEXT, UNIQUE(username, actividad))"))
        
        # 3. Crear tabla de configuración de usuario
        cursor.execute(fix_query("CREATE TABLE IF NOT EXISTS configuracion_usuario (username TEXT, clave TEXT, valor TEXT, PRIMARY KEY (username, clave))"))
        
        # 4. Crear tabla de listas globales (ubicaciones, tipos, medios, actividades globales)
        cursor.execute(fix_query("CREATE TABLE IF NOT EXISTS listas_globales (tipo TEXT, valor TEXT, UNIQUE(tipo, valor))"))
        
        # 5. Crear tabla de registros
        query_registros = """
            CREATE TABLE IF NOT EXISTS registros (
                id SERIAL PRIMARY KEY,
                usuario TEXT, tipo_actividad TEXT, fecha TIMESTAMP, dependencia TEXT,
                solicitante TEXT, tipo_solicitud TEXT, medio_solicitud TEXT,
                descripcion TEXT, cumplido TEXT, fecha_atencion TEXT, observaciones TEXT
            )
        """
        # Adaptar SERIAL para SQLite
        if not DATABASE_URL:
            query_registros = query_registros.replace('SERIAL PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT')
        
        cursor.execute(fix_query(query_registros))
        
        # 6. Asegurar usuario admin
        if DATABASE_URL:
            cursor.execute("INSERT INTO usuarios (username) VALUES (%s) ON CONFLICT DO NOTHING", ('admin',))
        else:
            cursor.execute("INSERT OR IGNORE INTO usuarios (username) VALUES (?)", ('admin',))
            
        # 7. Migración única desde JSON si la tabla está vacía
        cursor.execute("SELECT COUNT(*) as count FROM usuarios")
        count = cursor.fetchone()['count']
        if count <= 1 and os.path.exists(USERS_FILE):
             try:
                 logger.info(f"Iniciando migración desde {USERS_FILE}...")
                 with open(USERS_FILE, 'r', encoding='utf-8') as f:
                     data = json.load(f)
                 
                 # Migrar usuarios
                 for u in data.get("usuarios", []):
                     if u.lower() != 'admin':
                         if DATABASE_URL:
                             cursor.execute("INSERT INTO usuarios (username) VALUES (%s) ON CONFLICT DO NOTHING", (u,))
                         else:
                             cursor.execute("INSERT OR IGNORE INTO usuarios (username) VALUES (?)", (u,))
                 
                 # Migrar actividades personales
                 act_dict = data.get("actividades", {})
                 for user, acts in act_dict.items():
                     for act in acts:
                         if DATABASE_URL:
                             cursor.execute("INSERT INTO actividades_personales (username, actividad) VALUES (%s, %s) ON CONFLICT DO NOTHING", (user, act))
                         else:
                             cursor.execute("INSERT OR IGNORE INTO actividades_personales (username, actividad) VALUES (?, ?)", (user, act))
                 
                 # Migrar configuraciones (incluyendo datos_contrato)
                 conf_dict = data.get("configuraciones", {})
                 for user, conf in conf_dict.items():
                     for key, val in conf.items():
                         val_str = json.dumps(val, ensure_ascii=False)
                         if DATABASE_URL:
                             cursor.execute("INSERT INTO configuracion_usuario (username, clave, valor) VALUES (%s, %s, %s) ON CONFLICT (username, clave) DO UPDATE SET valor=EXCLUDED.valor", (user, key, val_str))
                         else:
                             cursor.execute("INSERT INTO configuracion_usuario (username, clave, valor) VALUES (?, ?, ?) ON CONFLICT(username, clave) DO UPDATE SET valor=excluded.valor", (user, key, val_str))
                 
                 logger.info("Migración desde JSON completada con éxito.")
             except Exception as me:
                 logger.error(f"Error durante la migración: {me}")
        
        # 8. Migración desde Excel si la tabla registros está vacía
        cursor.execute("SELECT COUNT(*) as count FROM registros")
        reg_count = cursor.fetchone()['count']
        if reg_count == 0 and os.path.exists(EXCEL_FILE):
            try:
                logger.info(f"Iniciando migración desde {EXCEL_FILE}...")
                # Leer excel, forzar string para evitar problemas de tipos
                df_excel = pd.read_excel(EXCEL_FILE, engine='openpyxl')
                
                # Mapeo inverso de columnas de Excel a SQL
                inv_col_map = {
                    "USUARIO": "usuario",
                    "TIPO DE ACTIVIDAD": "tipo_actividad",
                    "FECHA": "fecha",
                    "DEPENDENCIA": "dependencia",
                    "SOLICITANTE": "solicitante",
                    "TIPO DE SOLICITUD": "tipo_solicitud",
                    "MEDIO DE SOLICITUD": "medio_solicitud",
                    "DESCRIPCIÓN": "descripcion",
                    "CUMPLIDO": "cumplido",
                    "FECHA ATENCIÓN": "fecha_atencion",
                    "OBSERVACIONES": "observaciones"
                }
                
                for _, row in df_excel.iterrows():
                    vals = []
                    cols = []
                    for excel_col, sql_col in inv_col_map.items():
                        if excel_col in df_excel.columns:
                            val = row[excel_col]
                            # Manejar fechas de Pandas
                            if excel_col == "FECHA" and pd.notnull(val):
                                try:
                                    val = pd.to_datetime(val).strftime('%Y-%m-%d %H:%M:%S')
                                except:
                                    val = str(val)
                            else:
                                val = str(val) if pd.notnull(val) else ""
                            
                            vals.append(val)
                            cols.append(sql_col)
                    
                    if vals:
                        placeholders = ", ".join(["?"] * len(vals))
                        columnas_str = ", ".join(cols)
                        q = f"INSERT INTO registros ({columnas_str}) VALUES ({placeholders})"
                        cursor.execute(fix_query(q), tuple(vals))
                
                logger.info(f"Migración desde Excel completada. {len(df_excel)} registros importados.")
            except Exception as e_excel:
                logger.error(f"Error migrando Excel: {e_excel}")

        conn.commit()
        conn.close()
        logger.info("Base de datos inicializada correctamente.")
    except Exception as e:
        logger.error(f"Error crítico inicializando base de datos: {e}")

def inicializar_tablas_postgres():
    """Stub para compatibilidad, redirige a inicializar_tablas"""
    inicializar_tablas()

# =============================================================================
# FUNCIONES DE INICIALIZACIÓN (Stub para compatibilidad)
# =============================================================================

@medir_tiempo
def inicializar_usuarios():
    """Punto de entrada para inicialización desde app_web.py"""
    # 1. Asegurar tablas
    inicializar_tablas()
    
    # 2. Sincronización automática de registros desde Excel Compartido (Pull)
    # Solo si el Excel es externo/maestro o estamos en modo red
    importar_desde_excel()
    
    # 3. Limpiar caché inicial
    clear_cache()

def inicializar_config():
    pass

def inicializar_excel():
    pass

# =============================================================================
# CARGA DE USUARIOS
# =============================================================================

@cache_decorator
@medir_tiempo
def cargar_usuarios():
    """Carga usuarios y sus configuraciones/actividades desde SQLite"""
    try:
        conn = get_db_connection()
        cursor = get_cursor(conn)
        
        # Cargar usuarios
        cursor.execute("SELECT username FROM usuarios")
        usuarios = [row['username'] for row in cursor.fetchall()]
        
        # Cargar actividades personales
        actividades = {}
        cursor.execute("SELECT username, actividad FROM actividades_personales")
        for row in cursor.fetchall():
            user = row['username']
            if user not in actividades:
                actividades[user] = []
            actividades[user].append(row['actividad'])
            
        # Cargar configuraciones
        configuraciones = {}
        cursor.execute("SELECT username, clave, valor FROM configuracion_usuario")
        for row in cursor.fetchall():
            user = row['username']
            if user not in configuraciones:
                configuraciones[user] = {}
            try:
                configuraciones[user][row['clave']] = json.loads(row['valor'])
            except:
                 configuraciones[user][row['clave']] = row['valor']

        conn.close()
        
        return {
            "usuarios": usuarios if usuarios else ["admin"],
            "actividades": actividades,
            "configuraciones": configuraciones
        }
    except Exception as e:
        logger.error(f"Error cargando usuarios SQL: {e}")
        return {"usuarios": ["admin"]}

@medir_tiempo
def guardar_usuarios(data):
    """
    Sincroniza la lista de usuarios en la base de datos con la lista proporcionada.
    Agrega usuarios nuevos y elimina los que ya no están en la lista (excepto admin).
    """
    try:
        conn = get_db_connection()
        cursor = get_cursor(conn)
        
        new_users_set = set(data.get("usuarios", []))
        if "admin" not in new_users_set:
            new_users_set.add("admin") # Asegurar admin

        # 1. Obtener usuarios actuales en DB
        cursor.execute("SELECT username FROM usuarios")
        current_db_users = set(row['username'] for row in cursor.fetchall())

        # 2. Identificar a agregar y eliminar
        to_add = new_users_set - current_db_users
        to_remove = current_db_users - new_users_set

        # 3. Eliminar
        for user in to_remove:
            if user != 'admin': # Seguridad extra
                # Eliminar datos asociados para evitar huérfanos
                cursor.execute(fix_query("DELETE FROM actividades_personales WHERE username = ?"), (user,))
                cursor.execute(fix_query("DELETE FROM configuracion_usuario WHERE username = ?"), (user,))
                cursor.execute(fix_query("DELETE FROM usuarios WHERE username = ?"), (user,))

        # 4. Agregar
        for user in to_add:
            if DATABASE_URL:
                # Postgres: ON CONFLICT
                cursor.execute("INSERT INTO usuarios (username) VALUES (%s) ON CONFLICT DO NOTHING", (user,))
            else:
                # SQLite
                cursor.execute("INSERT OR IGNORE INTO usuarios (username) VALUES (?)", (user,))
        
        conn.commit()
        conn.close()
        clear_cache()
        sincronizar_db_a_master()
        return True
    except Exception as e:
        logger.error(f"Error sincronizando usuarios SQL: {e}")
        return False

@medir_tiempo
def obtener_configuracion_usuario(usuario):
    """Obtiene la configuración personalizada de un usuario"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # En el modelo actual, guardamos claves individuales.
        # Pero por compatibilidad, la función espera un dict completo de config.
        # Vamos a reconstruirlo.
        
        # Default config
        config = {
            "tema": "claro",
            "columnas_visibles": ["TIPO DE ACTIVIDAD", "FECHA", "DEPENDENCIA", "SOLICITANTE", "DESCRIPCIÓN", "CUMPLIDO"],
            "orden_por": "FECHA",
            "orden_direccion": "desc",
            "datos_contrato": {"objeto": "", "nro": "", "nombre": "", "cedula": "", "supervisor": ""}
        }

        cursor.execute(fix_query("SELECT clave, valor FROM configuracion_usuario WHERE username = ?"), (usuario,))
        rows = cursor.fetchall()
        for row in rows:
            try:
                config[row['clave']] = json.loads(row['valor'])
            except:
                pass
                
        conn.close()
        try:
            dc = config.get("datos_contrato", {}) or {}
            keys = ['objeto','nro','nombre','cedula','supervisor']
            if not any(dc.get(k) for k in keys):
                candidates = []
                for d in DIRS_SEARCH:
                    p = os.path.join(d, "usuarios.json")
                    if os.path.exists(p):
                        candidates.append(p)
                candidates.insert(0, USERS_FILE)
                seen = []
                uniq = [x for x in candidates if not (x in seen or seen.append(x))]
                found = None
                found_user = usuario
                for p in uniq:
                    try:
                        with open(p, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        for who in [usuario, 'admin']:
                            user_cfg = data.get('configuraciones', {}).get(who, {})
                            dc2 = user_cfg.get('datos_contrato')
                            if isinstance(dc2, dict) and any(dc2.get(k) for k in keys):
                                found = dc2
                                found_user = who
                                break
                        if found:
                            break
                    except Exception:
                        continue
                if isinstance(found, dict):
                    config['datos_contrato'] = found
                    try:
                        conn2 = get_db_connection()
                        cur2 = get_cursor(conn2)
                        val_str = json.dumps(found, ensure_ascii=False)
                        q = fix_query('''
                            INSERT INTO configuracion_usuario (username, clave, valor)
                            VALUES (?, ?, ?)
                            ON CONFLICT(username, clave) DO UPDATE SET valor=excluded.valor
                        ''')
                        cur2.execute(q, (usuario, 'datos_contrato', val_str))
                        conn2.commit()
                        conn2.close()
                    except Exception:
                        pass
        except Exception:
            pass
        return config
    except Exception as e:
        logger.error(f"Error obteniendo config usuario {usuario}: {e}")
        return {}

@medir_tiempo
def guardar_configuracion_usuario(usuario, config):
    """Guarda la configuración personalizada"""
    try:
        conn = get_db_connection()
        cursor = get_cursor(conn)
        
        for key, value in config.items():
            val_str = json.dumps(value, ensure_ascii=False)
            query = '''
                INSERT INTO configuracion_usuario (username, clave, valor) 
                VALUES (?, ?, ?)
                ON CONFLICT(username, clave) DO UPDATE SET valor=excluded.valor
            '''
            query = fix_query(query)
            cursor.execute(query, (usuario, key, val_str))
            
        conn.commit()
        conn.close()
        clear_cache()
        sincronizar_db_a_master()
        return True
    except Exception as e:
        logger.error(f"Error guardando config usuario {usuario}: {e}")
        return False

# =============================================================================
# GESTIÓN DIRECTA DE ACTIVIDADES PERSONALES (SQL)
# =============================================================================

def agregar_actividad_personal_db(usuario, actividad):
    """Agrega una actividad personal verificando duplicados"""
    try:
        conn = get_db_connection()
        cursor = get_cursor(conn)
        
        # Verificar si ya existe
        cursor.execute(fix_query("SELECT 1 FROM actividades_personales WHERE username = ? AND actividad = ?"), (usuario, actividad))
        if cursor.fetchone():
            conn.close()
            return False # Ya existe
            
        cursor.execute(fix_query("INSERT INTO actividades_personales (username, actividad) VALUES (?, ?)"), (usuario, actividad))
        conn.commit()
        conn.close()
        clear_cache()
        sincronizar_db_a_master()
        return True
    except Exception as e:
        logger.error(f"Error agregando actividad personal DB: {e}")
        return False

def eliminar_actividad_personal_db(usuario, actividad):
    try:
        conn = get_db_connection()
        cursor = get_cursor(conn)
        cursor.execute(fix_query("DELETE FROM actividades_personales WHERE username = ? AND actividad = ?"), (usuario, actividad))
        conn.commit()
        conn.close()
        clear_cache()
        sincronizar_db_a_master()
        return True
    except Exception as e:
        logger.error(f"Error eliminando actividad personal DB: {e}")
        return False

# =============================================================================
# CARGA DE CONFIGURACIÓN (Listas de opciones)
# =============================================================================

def _cargar_lista_global(tipo, default):
    try:
        with db_session() as conn:
            cursor = get_cursor(conn)
            cursor.execute(fix_query("SELECT valor FROM listas_globales WHERE tipo = ?"), (tipo,))
            rows = cursor.fetchall()
            return [row['valor'] for row in rows] if rows else default
    except Exception as e:
        logger.error(f"Error cargando lista {tipo}: {e}")
        return default

def _guardar_lista_global(tipo, lista):
    try:
        with db_session() as conn:
            cursor = get_cursor(conn)
            cursor.execute(fix_query("DELETE FROM listas_globales WHERE tipo = ?"), (tipo,))
            for val in lista:
                cursor.execute(fix_query("INSERT OR IGNORE INTO listas_globales (tipo, valor) VALUES (?, ?)"), (tipo, val))
        clear_cache()
        sincronizar_db_a_master()
        return True
    except Exception as e:
        logger.error(f"Error guardando lista {tipo}: {e}")
        return False

@cache_decorator
@medir_tiempo
def cargar_actividades_globales():
    return _cargar_lista_global('actividad', ACTIVIDADES_DEFAULT)

@cache_decorator
@medir_tiempo
def cargar_actividades(usuario=None):
    """
    Carga actividades disponibles.
    Solo retorna actividades personales del usuario.
    """
    try:
        personales = []
        
        # Si hay un usuario específico, cargar sus actividades personales
        if usuario:
            conn = get_db_connection()
            cursor = get_cursor(conn)
            cursor.execute(fix_query("SELECT actividad FROM actividades_personales WHERE username = ?"), (usuario,))
            personales = [row['actividad'] for row in cursor.fetchall()]
            conn.close()
            
        return sorted(list(set(personales)))
    except Exception as e:
        logger.error(f"Error cargando actividades para {usuario}: {e}")
        return []

@cache_decorator
@medir_tiempo
def cargar_ubicaciones():
    return _cargar_lista_global('ubicacion', UBICACIONES_DEFAULT)

@cache_decorator
@medir_tiempo
def cargar_tipos_solicitud():
    return _cargar_lista_global('tipo_solicitud', TIPOS_SOLICITUD_DEFAULT)

@cache_decorator
@medir_tiempo
def cargar_medios_solicitud():
    return _cargar_lista_global('medio_solicitud', MEDIOS_SOLICITUD_DEFAULT)

@medir_tiempo
def guardar_actividades(actividades):
    return _guardar_lista_global('actividad', actividades)

@medir_tiempo
def guardar_ubicaciones(ubicaciones):
    return _guardar_lista_global('ubicacion', ubicaciones)

@medir_tiempo
def guardar_tipos_solicitud(tipos):
    return _guardar_lista_global('tipo_solicitud', tipos)

@medir_tiempo
def guardar_medios_solicitud(medios):
    return _guardar_lista_global('medio_solicitud', medios)

# =============================================================================
# CRUD DE REGISTROS
# =============================================================================

@retry_operation(max_retries=3, base_delay=0.5)
def sincronizar_db_a_master():
    """Copia la base de datos local de vuelta a la carpeta de red (si existe) para que otros la vean"""
    if not MASTER_DIR or not os.path.exists(MASTER_DIR):
        return False
    
    import shutil
    try:
        dest = os.path.join(MASTER_DIR, os.path.basename(DB_FILE))
        # Solo copiar si el destino es diferente y escribible
        if os.path.abspath(DB_FILE) != os.path.abspath(dest):
            shutil.copy2(DB_FILE, dest)
            logger.info(f"[OK] Sincronización exitosa: BD copiada a red: {dest}")
            return True
    except Exception as e:
        logger.error(f"❌ Error sincronizando DB a master: {e}")
    return False

@retry_operation(max_retries=3, base_delay=0.5)
def sincronizar_excel():
    """Exporta todos los registros de la BD al archivo Excel para respaldo"""
    try:
        df = cargar_registros()
        # Eliminar columna ID si existe para que Excel se vea igual que antes
        df_export = df.drop(columns=['ID']) if 'ID' in df.columns else df
            
        # Reordenar columnas para que coincidan exactamente con la constante COLUMNAS (menos ID)
        cols_final = [c for c in COLUMNAS if c != 'ID']
        df_export = df_export[cols_final]
        
        # Intento de escritura resiliente
        intentos = 3
        exito = False
        while intentos > 0:
            try:
                # engine='openpyxl' es vital para la codificación correcta de tildes en xlsx
                df_export.to_excel(EXCEL_FILE, index=False, engine='openpyxl')
                logger.info(f"✅ Sincronización con Excel exitosa: {EXCEL_FILE}")
                exito = True
                break
            except PermissionError:
                intentos -= 1
                if intentos == 0:
                    logger.warning(f"[WARNING] No se pudo sincronizar Excel {EXCEL_FILE}: El archivo está abierto.")
                time.sleep(0.5)
            except Exception as ex:
                logger.error(f"[ERROR] Error inesperado sincronizando Excel: {ex}")
                break
        
        # v7.0: También sincronizar la DB a la red si estamos en modo local fallback
        sincronizar_db_a_master()
        
        return exito
    except Exception as e:
        logger.error(f"[ERROR] Error crítico en sincronizar_excel: {e}")
        return False

@retry_operation(max_retries=3)
def importar_desde_excel(file_path=None):
    """Importa y combina registros desde un archivo Excel externo (Maestro)"""
    if not file_path:
        file_path = EXCEL_FILE
        
    if not os.path.exists(file_path):
        logger.warning(f"[WARNING] No se puede importar: {file_path} no existe.")
        return 0
        
    try:
        logger.info(f"[RELOAD] Iniciando sincronización desde: {file_path}")
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # Limpieza y Mapeo Flexible de Columnas
        df.columns = [c.upper().strip() for c in df.columns]
        mapeo = {
            'ACTIVIDAD': 'TIPO DE ACTIVIDAD',
            'TIPO ACTIVIDAD': 'TIPO DE ACTIVIDAD',
            'UBICACION': 'DEPENDENCIA',
            'LUGAR': 'DEPENDENCIA',
            'SOLICITANTE': 'SOLICITANTE',
            'MEDIO': 'MEDIO DE SOLICITUD'
        }
        df = df.rename(columns=mapeo)
        
        # Asegurar columnas esperadas
        for col in COLUMNAS:
            if col not in df.columns:
                df[col] = ""
                
        count = 0
        with db_session() as conn:
            cursor = get_cursor(conn)
            for _, row in df.iterrows():
                try:
                    fecha = str(row.get('FECHA', ''))
                    fecha_atencion = str(row.get('FECHA ATENCIÓN', ''))
                    values = (
                        str(row.get('USUARIO', 'admin')),
                        str(row.get('TIPO DE ACTIVIDAD', '')),
                        fecha,
                        str(row.get('DEPENDENCIA', '')),
                        str(row.get('SOLICITANTE', '')),
                        str(row.get('TIPO DE SOLICITUD', '')),
                        str(row.get('MEDIO DE SOLICITUD', '')),
                        str(row.get('DESCRIPCIÓN', '')),
                        str(row.get('CUMPLIDO', '')),
                        fecha_atencion,
                        str(row.get('OBSERVACIONES', ''))
                    )
                    
                    # Comprobación de duplicado por clave de negocio
                    cursor.execute(fix_query('''
                        SELECT 1 FROM registros 
                        WHERE usuario=? AND tipo_actividad=? AND fecha=? AND descripcion=? 
                        LIMIT 1
                    '''), (values[0], values[1], values[2], values[7]))
                    
                    if cursor.fetchone():
                        continue
                        
                    cursor.execute(fix_query('''
                        INSERT INTO registros (
                            usuario, tipo_actividad, fecha, dependencia, solicitante,
                            tipo_solicitud, medio_solicitud, descripcion, cumplido,
                            fecha_atencion, observaciones
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    '''), values)
                    count += 1
                except Exception as e:
                    logger.error(f"Error importando fila: {e}")
                    
        if count > 0:
            logger.info(f"✅ Sincronización completada: Agregados {count} registros nuevos.")
            clear_cache()
        return count
    except Exception as e:
        logger.error(f"[ERROR] Error crítico importando desde Excel: {e}")
        return 0

@retry_operation(max_retries=3)
@medir_tiempo
def cargar_registros(usuario=None):
    try:
        conn = get_db_connection()
        query = "SELECT * FROM registros"
        params = []
        
        # v6.9: Filtro estricto por usuario para la tabla principal
        if usuario:
            query += " WHERE usuario = ?"
            params.append(usuario)
            
        if DATABASE_URL:
            query = query.replace('?', '%s')
            
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        # Mapeo de columnas SQL a nombres de Excel para compatibilidad
        col_map = {
            "id": "ID",
            "usuario": "USUARIO",
            "tipo_actividad": "TIPO DE ACTIVIDAD",
            "fecha": "FECHA",
            "dependencia": "DEPENDENCIA",
            "solicitante": "SOLICITANTE",
            "tipo_solicitud": "TIPO DE SOLICITUD",
            "medio_solicitud": "MEDIO DE SOLICITUD",
            "descripcion": "DESCRIPCIÓN",
            "cumplido": "CUMPLIDO",
            "fecha_atencion": "FECHA ATENCIÓN",
            "observaciones": "OBSERVACIONES"
        }
        df.rename(columns=col_map, inplace=True)
        # Asegurar columnas faltantes
        for col in COLUMNAS:
            if col not in df.columns:
                df[col] = ""
                
        return df.fillna('')
    except Exception as e:
        logger.error(f"Error cargando registros SQL: {e}")
        return pd.DataFrame(columns=COLUMNAS)

@retry_operation(max_retries=3)
@medir_tiempo
def guardar_registro(data):
    try:
        with db_session() as conn:
            cursor = get_cursor(conn)
            
            query = '''
                INSERT INTO registros (
                    usuario, tipo_actividad, fecha, dependencia, solicitante,
                    tipo_solicitud, medio_solicitud, descripcion, cumplido,
                    fecha_atencion, observaciones
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            insert_values = (
                data.get("USUARIO"),
                data.get("TIPO DE ACTIVIDAD"),
                data.get("FECHA"),
                data.get("DEPENDENCIA"),
                data.get("SOLICITANTE"),
                data.get("TIPO DE SOLICITUD"),
                data.get("MEDIO DE SOLICITUD"),
                data.get("DESCRIPCIÓN"),
                data.get("CUMPLIDO"),
                data.get("FECHA ATENCIÓN"),
                data.get("OBSERVACIONES")
            )
            
            if DATABASE_URL:
                # Postgres requiere RETURNING id para obtener el ID insertado
                query_pg = query.replace('?', '%s') + " RETURNING id"
                cursor.execute(query_pg, insert_values)
                nuevo_id = cursor.fetchone()['id']
            else:
                # SQLite usa lastrowid
                cursor.execute(query, insert_values)
                nuevo_id = cursor.lastrowid
                
        # Sincronizar con Excel después de guardar (fuera del bloque with para no bloquear la BD)
        sincronizar_excel()
        return nuevo_id
    except Exception as e:
        logger.error(f"Error guardando registro SQL: {e}")
        return None

@retry_operation(max_retries=3)
@medir_tiempo
def eliminar_registro(id_registro, usuario):
    try:
        with db_session() as conn:
            cursor = get_cursor(conn)
            
            # Verificar propiedad
            if usuario != "admin":
                cursor.execute(fix_query("SELECT usuario FROM registros WHERE id = ?"), (id_registro,))
                row = cursor.fetchone()
                if not row or row['usuario'] != usuario:
                    return False

            cursor.execute(fix_query("DELETE FROM registros WHERE id = ?"), (id_registro,))

        # Sincronizar con Excel después de eliminar
        sincronizar_excel()
        return True
    except Exception as e:
        logger.error(f"Error eliminando registro SQL: {e}")
        return False

@retry_operation(max_retries=3)
@medir_tiempo
def actualizar_registro(id_registro, data, usuario):
    try:
        with db_session() as conn:
            cursor = get_cursor(conn)
            
            # Verificar propiedad
            cursor.execute(fix_query("SELECT usuario FROM registros WHERE id = ?"), (id_registro,))
            row = cursor.fetchone()
            if not row:
                return False
                
            if usuario != "admin" and row['usuario'] != usuario:
                return False
                
            # Construir UPDATE dinámico
            inv_col_map = {
                "USUARIO": "usuario",
                "TIPO DE ACTIVIDAD": "tipo_actividad",
                "FECHA": "fecha",
                "DEPENDENCIA": "dependencia",
                "SOLICITANTE": "solicitante",
                "TIPO DE SOLICITUD": "tipo_solicitud",
                "MEDIO DE SOLICITUD": "medio_solicitud",
                "DESCRIPCIÓN": "descripcion",
                "CUMPLIDO": "cumplido",
                "FECHA ATENCIÓN": "fecha_atencion",
                "OBSERVACIONES": "observaciones"
            }
            
            fields = []
            values = []
            for key, value in data.items():
                if key in inv_col_map:
                    if key == 'USUARIO' and usuario != 'admin':
                        continue
                    fields.append(f"{inv_col_map[key]} = ?")
                    values.append(value)
            
            if not fields:
                return True
                
            values.append(id_registro)
            query = f"UPDATE registros SET {', '.join(fields)} WHERE id = ?"
            query = fix_query(query)

            cursor.execute(query, values)
            
        # Sincronizar con Excel después de actualizar
        sincronizar_excel()
        clear_cache()
        return True
    except Exception as e:
        logger.error(f"Error actualizando registro SQL: {e}")
        return False
