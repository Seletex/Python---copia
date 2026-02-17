"""
Módulo de base de datos: inicialización y operaciones CRUD básicas.
Las funciones de exportación están en export_service.py
Las funciones de actividades personales están en activity_service.py
"""

import os
import json
import pandas as pd
from config import (
    CONFIG_FILE, USERS_FILE, EXCEL_FILE,
    ACTIVIDADES_DEFAULT, UBICACIONES_DEFAULT,
    TIPOS_SOLICITUD_DEFAULT, MEDIOS_SOLICITUD_DEFAULT,
    COLUMNAS, logger
)
from utils import cache_decorator, medir_tiempo, clear_cache

# =============================================================================
# FUNCIONES DE INICIALIZACIÓN
# =============================================================================

@medir_tiempo
def inicializar_usuarios():
    """Inicializa el archivo de usuarios si no existe"""
    if not os.path.exists(USERS_FILE):
        usuarios_data = {
            "usuarios": ["admin"],
            "actividades": {"admin": []}
        }
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(usuarios_data, f, indent=2, ensure_ascii=False)

@medir_tiempo
def inicializar_config():
    """Inicializa el archivo de configuración si no existe"""
    if not os.path.exists(CONFIG_FILE):
        config_data = {
            "actividades": ACTIVIDADES_DEFAULT,
            "ubicaciones": UBICACIONES_DEFAULT,
            "tipos_actividad": TIPOS_SOLICITUD_DEFAULT,
            "medios_solicitud": MEDIOS_SOLICITUD_DEFAULT,
            "dependencias": []
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

@medir_tiempo
def inicializar_excel():
    """Inicializa el archivo Excel si no existe"""
    if not os.path.exists(EXCEL_FILE):
        df = pd.DataFrame(columns=COLUMNAS)
        df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')

# =============================================================================
# CARGA DE USUARIOS
# =============================================================================

@cache_decorator
@medir_tiempo
def cargar_usuarios():
    """Carga la lista de usuarios desde el archivo JSON"""
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"usuarios": ["admin"]}
    except Exception:
        return {"usuarios": ["admin"]}

@medir_tiempo
def guardar_usuarios(data):
    """Guarda los datos de usuarios en el archivo JSON"""
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        clear_cache()
        return True
    except Exception as e:
        logger.error(f"Error guardando usuarios: {e}")
        return False

@medir_tiempo
def obtener_configuracion_usuario(usuario):
    """Obtiene la configuración personalizada de un usuario"""
    usuarios_data = cargar_usuarios()
    configuraciones = usuarios_data.get("configuraciones", {})
    if usuario in configuraciones:
        config = configuraciones[usuario]
        if "datos_contrato" not in config:
            config["datos_contrato"] = {"objeto": "", "nro": "", "nombre": "", "cedula": "", "supervisor": ""}
        elif "supervisor" not in config["datos_contrato"]:
            config["datos_contrato"]["supervisor"] = ""
        return config
    return {
        "tema": "claro",
        "columnas_visibles": ["TIPO DE ACTIVIDAD", "FECHA", "DEPENDENCIA", "SOLICITANTE", "DESCRIPCIÓN", "CUMPLIDO"],
        "orden_por": "FECHA",
        "orden_direccion": "desc",
        "datos_contrato": {"objeto": "", "nro": "", "nombre": "", "cedula": "", "supervisor": ""}
    }

@medir_tiempo
def guardar_configuracion_usuario(usuario, config):
    """Guarda la configuración personalizada de un usuario"""
    try:
        usuarios_data = cargar_usuarios()
        if "configuraciones" not in usuarios_data:
            usuarios_data["configuraciones"] = {}
        usuarios_data["configuraciones"][usuario] = config
        return guardar_usuarios(usuarios_data)
    except Exception as e:
        logger.error(f"Error guardando configuración de usuario {usuario}: {e}")
        return False

# =============================================================================
# CARGA DE CONFIGURACIÓN (Listas de opciones)
# =============================================================================

def _cargar_campo_config(campo, default):
    """Helper genérico para cargar un campo del archivo de configuración"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get(campo, default)
        return default
    except Exception:
        return default

def _guardar_campo_config(campo, valor):
    """Helper genérico para guardar un campo en el archivo de configuración"""
    try:
        config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        config[campo] = valor
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        clear_cache()
        return True
    except Exception as e:
        logger.error(f"Error guardando {campo}: {e}")
        return False

@cache_decorator
@medir_tiempo
def cargar_actividades_globales():
    """Carga solo las actividades globales"""
    return _cargar_campo_config('actividades', ACTIVIDADES_DEFAULT)

@cache_decorator
@medir_tiempo
def cargar_actividades(usuario=None):
    """Carga actividades globales + personales del usuario"""
    try:
        actividades_globales = cargar_actividades_globales()
        actividades_usuario = []
        if usuario and os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                users_config = json.load(f)
                actividades_usuario = users_config.get("actividades", {}).get(usuario, [])
        return sorted(list(set(actividades_globales + actividades_usuario)))
    except Exception:
        return ACTIVIDADES_DEFAULT

@cache_decorator
@medir_tiempo
def cargar_ubicaciones():
    return _cargar_campo_config('ubicaciones', UBICACIONES_DEFAULT)

@cache_decorator
@medir_tiempo
def cargar_tipos_solicitud():
    return _cargar_campo_config('tipos_actividad', TIPOS_SOLICITUD_DEFAULT)

@cache_decorator
@medir_tiempo
def cargar_medios_solicitud():
    return _cargar_campo_config('medios_solicitud', MEDIOS_SOLICITUD_DEFAULT)

@medir_tiempo
def guardar_actividades(actividades):
    return _guardar_campo_config('actividades', actividades)

@medir_tiempo
def guardar_ubicaciones(ubicaciones):
    return _guardar_campo_config('ubicaciones', ubicaciones)

@medir_tiempo
def guardar_tipos_solicitud(tipos):
    return _guardar_campo_config('tipos_actividad', tipos)

@medir_tiempo
def guardar_medios_solicitud(medios):
    return _guardar_campo_config('medios_solicitud', medios)

# =============================================================================
# CRUD DE REGISTROS (Excel)
# =============================================================================

@medir_tiempo
def cargar_registros(usuario=None):
    """Carga registros del Excel, filtra por usuario si no es admin"""
    try:
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
            if usuario and usuario != "admin" and 'USUARIO' in df.columns:
                df = df[df['USUARIO'] == usuario]
            return df.fillna('')
        return pd.DataFrame(columns=COLUMNAS)
    except Exception as e:
        logger.error(f"Error cargando registros: {e}")
        return pd.DataFrame(columns=COLUMNAS)

@medir_tiempo
def guardar_registro(data):
    """Guarda un nuevo registro en el archivo Excel calculando el ID"""
    try:
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
        else:
            df = pd.DataFrame(columns=COLUMNAS)
        
        # Calcular nuevo ID
        nuevo_id = 1 if df.empty else int(df["ID"].max()) + 1
        data["ID"] = nuevo_id
        
        nuevo_registro = pd.DataFrame([data])
        df_final = pd.concat([df, nuevo_registro], ignore_index=True)
        df_final.to_excel(EXCEL_FILE, index=False, engine='openpyxl')
        return nuevo_id
    except Exception as e:
        logger.error(f"Error guardando registro: {e}")
        return None

@medir_tiempo
def eliminar_registro(id_registro, usuario):
    """Elimina un registro por ID verificando propiedad (admin puede borrar cualquiera)"""
    try:
        if not os.path.exists(EXCEL_FILE):
            return False
            
        df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
        if id_registro not in df['ID'].values:
            return False
            
        registro = df[df['ID'] == id_registro].iloc[0]
        if usuario != "admin" and registro['USUARIO'] != usuario:
            logger.warning(f"Intento de eliminación no autorizada: {usuario} sobre ID {id_registro}")
            return False
            
        df = df[df['ID'] != id_registro]
        df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')
        return True
    except Exception as e:
        logger.error(f"Error eliminando registro: {e}")
        return False

@medir_tiempo
def actualizar_registro(id_registro, data, usuario):
    """Actualiza un registro verificando propiedad"""
    try:
        if not os.path.exists(EXCEL_FILE):
            return False
            
        df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
        if id_registro not in df['ID'].values:
            return False
            
        registro_idx = df.index[df['ID'] == id_registro].tolist()[0]
        propietario = df.at[registro_idx, 'USUARIO']
        
        if usuario != "admin" and propietario != usuario:
            logger.warning(f"Intento de actualización no autorizada: {usuario} sobre ID {id_registro}")
            return False
            
        # Actualizar campos (excepto ID y USUARIO si no es admin)
        for key, value in data.items():
            if key in COLUMNAS:
                if key == 'USUARIO' and usuario != 'admin':
                    continue
                df.at[registro_idx, key] = value
                
        df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')
        return True
    except Exception as e:
        logger.error(f"Error actualizando registro: {e}")
        return False