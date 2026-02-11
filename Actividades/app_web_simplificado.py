"""
Aplicación Web de Gestión de Actividades - Versión Simplificada
Versión modular con estructura organizada y reducida complejidad
"""

import os
from http.server import HTTPServer

# Importar módulos creados
from config import (
    CONFIG_FILE, USERS_FILE, EXCEL_FILE, logger
)
from database import (
    inicializar_usuarios, inicializar_config, inicializar_excel
)
from handlers import RequestHandler

def main():
    """Función principal de la aplicación"""
    try:
        # Inicializar archivos necesarios
        logger.info("Inicializando archivos de configuración...")
        inicializar_usuarios()
        inicializar_config()
        inicializar_excel()
        
        # Configurar servidor
        puerto = 8000
        direccion = ('', puerto)
        
        logger.info(f"Iniciando servidor en http://localhost:{puerto}")
        logger.info("Presiona Ctrl+C para detener el servidor")
        
        # Iniciar servidor
        with HTTPServer(direccion, RequestHandler) as servidor:
            servidor.serve_forever()
            
    except KeyboardInterrupt:
        logger.info("Servidor detenido por el usuario")
    except Exception as e:
        logger.error(f"Error iniciando servidor: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()