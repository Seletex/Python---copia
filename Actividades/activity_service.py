"""
Servicio de gestión de actividades personales por usuario.
Separado de database.py para responsabilidad única.
"""

from config import logger
from database import cargar_usuarios, guardar_usuarios
from utils import cache_decorator, medir_tiempo


@medir_tiempo
def agregar_actividad_personal(usuario, actividad):
    """Agrega una actividad personal para un usuario específico"""
    try:
        usuarios_data = cargar_usuarios()
        
        if "actividades" not in usuarios_data:
            usuarios_data["actividades"] = {}
        if usuario not in usuarios_data["actividades"]:
            usuarios_data["actividades"][usuario] = []
        
        if actividad not in usuarios_data["actividades"][usuario]:
            usuarios_data["actividades"][usuario].append(actividad)
            return guardar_usuarios(usuarios_data)
        
        return False
    except Exception as e:
        logger.error(f"Error agregando actividad personal: {e}")
        return False


@medir_tiempo
def eliminar_actividad_personal(usuario, actividad):
    """Elimina una actividad personal de un usuario"""
    try:
        usuarios_data = cargar_usuarios()
        
        actividades = usuarios_data.get("actividades", {}).get(usuario, [])
        if actividad in actividades:
            actividades.remove(actividad)
            return guardar_usuarios(usuarios_data)
        
        return False
    except Exception as e:
        logger.error(f"Error eliminando actividad personal: {e}")
        return False


@cache_decorator
@medir_tiempo
def obtener_actividades_personales(usuario):
    """Obtiene las actividades personales de un usuario"""
    try:
        usuarios_data = cargar_usuarios()
        return usuarios_data.get("actividades", {}).get(usuario, [])
    except Exception as e:
        logger.error(f"Error obteniendo actividades personales: {e}")
        return []
