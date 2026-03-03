"""
Módulo de utilidades de datos para la aplicación de escritorio (Tkinter).
Contiene funciones para manejar configuración, usuarios y registros.
Re-exporta constantes desde config.py para compatibilidad.
"""

import os
import json
from datetime import datetime
import pandas as pd

# Intentar importar tkinter, si falla (en servidor), definir mocks
try:
    from tkinter import messagebox
except ImportError:
    messagebox = None

from config import (
    EXCEL_FILE as FILE_NAME,
    CONFIG_FILE, USERS_FILE, COLUMNAS,
    ACTIVIDADES_DEFAULT, UBICACIONES_DEFAULT,
    TIPOS_SOLICITUD_DEFAULT, MEDIOS_SOLICITUD_DEFAULT
)

# Re-exportaciones para compatibilidad con AplicacionActividades.py
OPCIONES_CUMPLIDA = ["Sí", "No", "En Proceso"]

DEFAULTS = {
    "tipos_solicitud": TIPOS_SOLICITUD_DEFAULT,
    "medios_solicitud": MEDIOS_SOLICITUD_DEFAULT,
    "tipos_actividad": ACTIVIDADES_DEFAULT,
    "dependencias": UBICACIONES_DEFAULT
}

DEFAULT_USERS = {
    "usuarios": ["admin", "usuario1", "usuario2", "usuario3"],
    "configuraciones": {}
}

# =============================================================================
# INICIALIZACIÓN
# =============================================================================

def inicializar_config():
    """Crea el archivo de configuración si no existe"""
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULTS, f, ensure_ascii=False, indent=4)

def inicializar_usuarios():
    """Crea el archivo de usuarios si no existe"""
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_USERS, f, ensure_ascii=False, indent=4)

def inicializar_excel():
    """Crea el archivo Excel si no existe"""
    if not os.path.exists(FILE_NAME):
        df = pd.DataFrame(columns=COLUMNAS)
        df.to_excel(FILE_NAME, index=False)

# =============================================================================
# CARGA Y GUARDADO DE CONFIGURACIÓN
# =============================================================================

def _cargar_json(filepath, default):
    """Helper genérico para cargar archivos JSON"""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return default.copy()
    return default.copy()

def _guardar_json(filepath, data, error_title="Error"):
    """Helper genérico para guardar archivos JSON"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        if messagebox:
            messagebox.showerror(error_title, f"No se pudo guardar: {e}")
        return False

def cargar_config():
    return _cargar_json(CONFIG_FILE, DEFAULTS)

def cargar_usuarios():
    return _cargar_json(USERS_FILE, DEFAULT_USERS)

def guardar_config(config):
    return _guardar_json(CONFIG_FILE, config, "Error de Configuración")

def guardar_usuarios(usuarios_data):
    return _guardar_json(USERS_FILE, usuarios_data, "Error de Usuarios")

# =============================================================================
# GESTIÓN DE ITEMS DE CONFIGURACIÓN
# =============================================================================

def agregar_item_config(categoria, item):
    """Agrega un nuevo item a una categoría"""
    config = cargar_config()
    if item and item not in config.get(categoria, []):
        config.setdefault(categoria, []).append(item)
        if categoria == "dependencias":
            config[categoria].sort()
        return guardar_config(config)
    return False

def eliminar_item_config(categoria, item):
    """Elimina un item de una categoría"""
    config = cargar_config()
    items = config.get(categoria, [])
    if item in items:
        items.remove(item)
        return guardar_config(config)
    return False

def actualizar_item_config(categoria, valor_original, nuevo_valor):
    """Actualiza un item en una categoría"""
    config = cargar_config()
    items = config.get(categoria, [])
    items_upper = [x.upper() for x in items]
    
    if nuevo_valor.upper() in items_upper and nuevo_valor.upper() != valor_original.upper():
        return False
    try:
        index = items_upper.index(valor_original.upper())
        items[index] = nuevo_valor
        if categoria == "dependencias":
            items.sort()
        return guardar_config(config)
    except ValueError:
        return False

# =============================================================================
# CRUD DE REGISTROS (Excel)
# =============================================================================

def guardar_registro(data):
    """Guarda un nuevo registro en el Excel"""
    try:
        df = pd.read_excel(FILE_NAME) if os.path.exists(FILE_NAME) else pd.DataFrame(columns=COLUMNAS)
        nuevo_id = 1 if df.empty else int(df["ID"].max()) + 1
        data["ID"] = nuevo_id
        df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
        df.to_excel(FILE_NAME, index=False)
        return nuevo_id
    except Exception as e:
        if messagebox:
            messagebox.showerror("Error", f"Error al guardar: {str(e)}")
        return None

def cargar_registros(usuario=None):
    """Carga registros del Excel, filtrando por usuario si no es admin"""
    try:
        if os.path.exists(FILE_NAME):
            df = pd.read_excel(FILE_NAME)
            if usuario and usuario != "admin":
                df = df[df["USUARIO"] == usuario]
            return df
        return pd.DataFrame(columns=COLUMNAS)
    except Exception as e:
        if messagebox:
            messagebox.showerror("Error", f"Error al cargar registros: {str(e)}")
        return pd.DataFrame(columns=COLUMNAS)

def buscar_registros(termino, usuario=None):
    """Busca registros por término"""
    df = cargar_registros(usuario)
    if df.empty:
        return df
    mask = df.astype(str).apply(lambda x: x.str.contains(termino, case=False, na=False)).any(axis=1)
    return df[mask]

def eliminar_registro(id_registro, usuario=None):
    """Elimina un registro por ID verificando permisos"""
    try:
        df = cargar_registros()
        if not any(df["ID"] == id_registro):
            return False
        registro = df[df["ID"] == id_registro].iloc[0]
        if usuario != "admin" and registro["USUARIO"] != usuario:
            if messagebox:
                messagebox.showerror("Error", "No tienes permiso para eliminar este registro")
            return False
        df = df[df["ID"] != id_registro]
        df.to_excel(FILE_NAME, index=False)
        return True
    except Exception as e:
        if messagebox:
            messagebox.showerror("Error", f"Error al eliminar: {str(e)}")
        return False

def actualizar_registro(id_registro, data, usuario=None):
    """Actualiza un registro existente verificando permisos"""
    try:
        df = cargar_registros()
        if not any(df["ID"] == id_registro):
            return False
        registro = df[df["ID"] == id_registro].iloc[0]
        if usuario != "admin" and registro["USUARIO"] != usuario:
            if messagebox:
                messagebox.showerror("Error", "No tienes permiso para actualizar este registro")
            return False
        for key, value in data.items():
            df.loc[df["ID"] == id_registro, key] = value
        df.to_excel(FILE_NAME, index=False)
        return True
    except Exception as e:
        if messagebox:
            messagebox.showerror("Error", f"Error al actualizar: {str(e)}")
        return False
