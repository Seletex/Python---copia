
import sqlite3
import os
from config import logger, DB_FILE

def init_db():
    """Inicializa la base de datos SQLite con las tablas necesarias"""
    if os.path.exists(DB_FILE):
        logger.info(f"La base de datos {DB_FILE} ya existe.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Tabla de Usuarios
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            username TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Tabla de Configuración de Usuario (JSON stores)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracion_usuario (
            username TEXT,
            clave TEXT,
            valor TEXT,
            PRIMARY KEY (username, clave),
            FOREIGN KEY(username) REFERENCES usuarios(username)
        )
        ''')

        # Tabla de Listas Globales (Actividades, Ubicaciones, etc.)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS listas_globales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            valor TEXT NOT NULL,
            UNIQUE(tipo, valor)
        )
        ''')

        # Tabla de Actividades Personales
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS actividades_personales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            actividad TEXT NOT NULL,
            FOREIGN KEY(username) REFERENCES usuarios(username),
            UNIQUE(username, actividad)
        )
        ''')

        # Tabla de Registros (Actividades Realizadas)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            tipo_actividad TEXT,
            fecha TEXT,
            dependencia TEXT,
            solicitante TEXT,
            tipo_solicitud TEXT,
            medio_solicitud TEXT,
            descripcion TEXT,
            cumplido TEXT,
            fecha_atencion TEXT,
            observaciones TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(usuario) REFERENCES usuarios(username)
        )
        ''')

        conn.commit()
        logger.info("Base de datos SQLite inicializada correctamente.")
        print(f"Base de datos {DB_NAME} creada con éxito.")

    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
