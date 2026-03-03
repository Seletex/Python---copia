
"""
Módulo de base de datos SQLITE: reemplaza la versión basada en archivos.
Implementa la misma interfaz que database.py pero usando SQLite.
"""

import os
import json
import sqlite3
import pandas as pd
from config import (
    COLUMNAS, logger, ACTIVIDADES_DEFAULT, UBICACIONES_DEFAULT,
    TIPOS_SOLICITUD_DEFAULT, MEDIOS_SOLICITUD_DEFAULT
)
from utils import cache_decorator, medir_tiempo, clear_cache

DB_NAME = "actividades.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# =============================================================================
# FUNCIONES DE INICIALIZACIÓN (Stub para compatibilidad)
# =============================================================================

def inicializar_usuarios():
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
        cursor = conn.cursor()
        
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
    Guarda usuarios. Nota: En la versión SQL, esto es más complejo porque 'data' 
    es todo el JSON gigante. Lo ideal sería refactorizar para no guardar TODO.
    Por compatibilidad, implementamos algo básico o asumimos que se llaman a funciones específicas.
    """
    # En esta arquitectura migrada, guardar_usuarios se usa poco directamente,
    # más bien se usa agregar_usuario, etc. 
    # Si se usa para agregar un usuario nuevo:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        current_users = data.get("usuarios", [])
        for user in current_users:
            cursor.execute("INSERT OR IGNORE INTO usuarios (username) VALUES (?)", (user,))
        
        conn.commit()
        conn.close()
        clear_cache()
        return True
    except Exception as e:
        logger.error(f"Error guardando usuarios SQL: {e}")
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

        cursor.execute("SELECT clave, valor FROM configuracion_usuario WHERE username = ?", (usuario,))
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
        cursor = conn.cursor()
        
        for key, value in config.items():
            val_str = json.dumps(value, ensure_ascii=False)
            cursor.execute('''
                INSERT INTO configuracion_usuario (username, clave, valor) 
                VALUES (?, ?, ?)
                ON CONFLICT(username, clave) DO UPDATE SET valor=excluded.valor
            ''', (usuario, key, val_str))
            
        conn.commit()
        conn.close()
        clear_cache()
        return True
    except Exception as e:
        logger.error(f"Error guardando config usuario {usuario}: {e}")
        return False

# =============================================================================
# CARGA DE CONFIGURACIÓN (Listas de opciones)
# =============================================================================

def _cargar_lista_global(tipo, default):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT valor FROM listas_globales WHERE tipo = ?", (tipo,))
        resultado = [row['valor'] for row in cursor.fetchall()]
        conn.close()
        return resultado if resultado else default
    except Exception:
        return default

def _guardar_lista_global(tipo, lista):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Transacción: borrar previos del tipo e insertar nuevos 
        # (para mantener consistencia con la lógica de "guardar lista completa")
        cursor.execute("DELETE FROM listas_globales WHERE tipo = ?", (tipo,))
        for item in lista:
            cursor.execute("INSERT INTO listas_globales (tipo, valor) VALUES (?, ?)", (tipo, item))
        conn.commit()
        conn.close()
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
    try:
        globales = cargar_actividades_globales()
        personales = []
        if usuario:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT actividad FROM actividades_personales WHERE username = ?", (usuario,))
            personales = [row['actividad'] for row in cursor.fetchall()]
            conn.close()
        return sorted(list(set(globales + personales)))
    except Exception:
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

@medir_tiempo
def cargar_registros(usuario=None):
    try:
        conn = get_db_connection()
        query = "SELECT * FROM registros"
        params = []
        
        if usuario and usuario != "admin":
            query += " WHERE usuario = ?"
            params.append(usuario)
            
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
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO registros (
                usuario, tipo_actividad, fecha, dependencia, solicitante,
                tipo_solicitud, medio_solicitud, descripcion, cumplido,
                fecha_atencion, observaciones
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
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
        ))
        
        nuevo_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return nuevo_id
    except Exception as e:
        logger.error(f"Error guardando registro SQL: {e}")
        return None

@medir_tiempo
def eliminar_registro(id_registro, usuario):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar propiedad
        if usuario != "admin":
            cursor.execute("SELECT usuario FROM registros WHERE id = ?", (id_registro,))
            row = cursor.fetchone()
            if not row or row['usuario'] != usuario:
                conn.close()
                return False

        cursor.execute("DELETE FROM registros WHERE id = ?", (id_registro,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error eliminando registro SQL: {e}")
        return False

@medir_tiempo
def actualizar_registro(id_registro, data, usuario):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar propiedad
        cursor.execute("SELECT usuario FROM registros WHERE id = ?", (id_registro,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False
            
        if usuario != "admin" and row['usuario'] != usuario:
            conn.close()
            return False
            
        # Construir UPDATE dinámico
        # Mapeo inverso de Excel a SQL
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
            conn.close()
            return True
            
        values.append(id_registro)
        query = f"UPDATE registros SET {', '.join(fields)} WHERE id = ?"
        
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error actualizando registro SQL: {e}")
        return False
