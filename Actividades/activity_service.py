"""
Servicio de gestión de actividades personales por usuario.
Separado de database.py para responsabilidad única.
"""

from config import logger
from database import cargar_usuarios, agregar_actividad_personal_db, eliminar_actividad_personal_db
from utils import cache_decorator, medir_tiempo


@medir_tiempo
def agregar_actividad_personal(usuario, actividad):
    """Agrega una actividad personal para un usuario específico"""
    # Usamos la función optimizada de base de datos
    # Retorna True si se agregó, False si ya existía o hubo error
    return agregar_actividad_personal_db(usuario, actividad)


@medir_tiempo
def eliminar_actividad_personal(usuario, actividad):
    """Elimina una actividad personal de un usuario"""
    return eliminar_actividad_personal_db(usuario, actividad)


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
