"""
Módulo de utilidades y decoradores para la aplicación.
Solo contiene decoradores de cache y medición de rendimiento.
"""

import functools
import time
from config import logger, _CACHE, _CACHE_TIMEOUT


def cache_decorator(func):
    """Decorador para cachear resultados de funciones"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
        current_time = time.time()
        
        if cache_key in _CACHE:
            cached_value, expiry_time = _CACHE[cache_key]
            if current_time < expiry_time:
                return cached_value
        
        result = func(*args, **kwargs)
        _CACHE[cache_key] = (result, current_time + _CACHE_TIMEOUT)
        return result
    return wrapper


def clear_cache():
    """Limpia todo el cache de resultados"""
    _CACHE.clear()


def medir_tiempo(func):
    """Decorador para medir y loguear tiempo de ejecución"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        inicio = time.time()
        resultado = func(*args, **kwargs)
        tiempo_ms = (time.time() - inicio) * 1000
        
        logger.info(
            f"FUNCIÓN: {func.__name__} - TIEMPO: {tiempo_ms:.2f}ms - "
            f"ARGUMENTOS: {len(args)} args, {len(kwargs)} kwargs"
        )
        
        if tiempo_ms > 500:
            logger.warning(f"FUNCIÓN LENTA: {func.__name__} tomó {tiempo_ms:.2f}ms")
        
        return resultado
    return wrapper