
"""
Módulo de base de datos SQLITE: reemplaza la versión basada en archivos.
Implementa la misma interfaz que database.py pero usando SQLite.
"""

import os
import json
import sqlite3
import pandas as pd
from config import (
    EXCEL_FILE, USERS_FILE, CONFIG_FILE, DB_FILE, DATABASE_URL, COLUMNAS, 
    ACTIVIDADES_DEFAULT, UBICACIONES_DEFAULT, TIPOS_SOLICITUD_DEFAULT, MEDIOS_SOLICITUD_DEFAULT,
    logger
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

def get_db_connection():
    """Obtiene conexión a BD (PostgreSQL si hay URL, sino SQLite)"""
    if DATABASE_URL and psycopg2:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            return conn
        except Exception as e:
            logger.error(f"Error conectando a Postgres: {e}")
            # Fallback a SQLite si falla Postgres (opcional)
            
    # Timeout aumentado para evitar bloqueos en cargas pesadas
    conn = sqlite3.connect(DB_FILE, timeout=20)
    conn.row_factory = sqlite3.Row
    # Habilitar Write-Ahead Logging para mejor concurrencia
    conn.execute("PRAGMA journal_mode=WAL")
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
                df_excel = pd.read_excel(EXCEL_FILE)
                
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
    inicializar_tablas()
    
    # En Render, aseguramos que las tablas existan al inicio (ya manejado en inicializar_tablas)
    pass

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
    v6.8: Los usuarios normales NO ven las actividades personales de admin.
    """
    try:
        globales = cargar_actividades_globales()
        personales = []
        
        # Si hay un usuario específico, cargar sus actividades personales
        if usuario:
            conn = get_db_connection()
            cursor = get_cursor(conn)
            cursor.execute(fix_query("SELECT actividad FROM actividades_personales WHERE username = ?"), (usuario,))
            personales = [row['actividad'] for row in cursor.fetchall()]
            conn.close()
            
        # Retornar la unión de globales + personales del usuario actual
        # Esto previene que otros usuarios vean las actividades de 'admin' que no sean globales.
        return sorted(list(set(globales + personales)))
    except Exception as e:
        logger.error(f"Error cargando actividades para {usuario}: {e}")
        return ACTIVIDADES_DEFAULT

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

def sincronizar_excel():
    """Exporta todos los registros de la BD al archivo Excel para respaldo"""
    try:
        df = cargar_registros()
        # Eliminar columna ID si existe para que Excel se vea igual que antes
        if 'ID' in df.columns:
            df_export = df.drop(columns=['ID'])
        else:
            df_export = df
            
        # Reordenar columnas para que coincidan exactamente con la constante COLUMNAS (menos ID)
        cols_final = [c for c in COLUMNAS if c != 'ID']
        df_export = df_export[cols_final]
        
        # Intento de escritura resiliente
        intentos = 3
        while intentos > 0:
            try:
                df_export.to_excel(EXCEL_FILE, index=False)
                logger.info(f"Sincronización con Excel exitosa: {EXCEL_FILE}")
                break
            except PermissionError:
                intentos -= 1
                if intentos == 0:
                    logger.warning(f"No se pudo sincronizar Excel {EXCEL_FILE}: El archivo está abierto por otro programa.")
                import time
                time.sleep(0.5)
            except Exception as ex:
                logger.error(f"Error inesperado sincronizando Excel {EXCEL_FILE}: {ex}")
                break
    except Exception as e:
        logger.error(f"Error crítico en sincronizar_excel: {e}")

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
        return True
    except Exception as e:
        logger.error(f"Error actualizando registro SQL: {e}")
        return False
