
import sqlite3
import pandas as pd
import json
import os
from config import (
    CONFIG_FILE, USERS_FILE, EXCEL_FILE, logger, DB_FILE
)

def migrate_data():
    if not os.path.exists(DB_FILE):
        print(f"Error: La base de datos {DB_FILE} no existe. Ejecuta database_setup.py primero.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # 1. Migrar Usuarios y Actividades Personales
        print("Migrando usuarios y configuraciones...")
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
                
                # Usuarios
                for user in users_data.get("usuarios", []):
                    cursor.execute("INSERT OR IGNORE INTO usuarios (username) VALUES (?)", (user,))
                
                # Actividades Personales
                actividades_personales = users_data.get("actividades", {})
                for user, acts in actividades_personales.items():
                    for act in acts:
                        cursor.execute("INSERT OR IGNORE INTO actividades_personales (username, actividad) VALUES (?, ?)", (user, act))
                
                # Configuraciones
                configuraciones = users_data.get("configuraciones", {})
                for user, config in configuraciones.items():
                    for key, value in config.items():
                        val_str = json.dumps(value, ensure_ascii=False)
                        cursor.execute("INSERT OR IGNORE INTO configuracion_usuario (username, clave, valor) VALUES (?, ?, ?)", (user, key, val_str))

        # 2. Migrar Configuración Global (Listas)
        print("Migrando listas globales...")
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
                tipo_map = {
                    "actividades": "actividad",
                    "ubicaciones": "ubicacion",
                    "tipos_actividad": "tipo_solicitud",
                    "medios_solicitud": "medio_solicitud"
                }

                for json_key, db_type in tipo_map.items():
                    items = config_data.get(json_key, [])
                    for item in items:
                        cursor.execute("INSERT OR IGNORE INTO listas_globales (tipo, valor) VALUES (?, ?)", (db_type, item))

        # 3. Migrar Registros (Excel)
        print("Migrando registros desde Excel...")
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
            
            # Normalizar nombres de columnas
            df.columns = [c.upper().strip() for c in df.columns]
            
            registros_count = 0
            for _, row in df.iterrows():
                try:
                    fecha = str(row.get('FECHA', ''))
                    fecha_atencion = str(row.get('FECHA ATENCIÓN', ''))
                    
                    cursor.execute('''
                        INSERT INTO registros (
                            usuario, tipo_actividad, fecha, dependencia, solicitante,
                            tipo_solicitud, medio_solicitud, descripcion, cumplido,
                            fecha_atencion, observaciones
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row.get('USUARIO', 'admin'), # Default to admin if missing
                        row.get('TIPO DE ACTIVIDAD', ''),
                        fecha,
                        row.get('DEPENDENCIA', ''),
                        row.get('SOLICITANTE', ''),
                        row.get('TIPO DE SOLICITUD', ''),
                        row.get('MEDIO DE SOLICITUD', ''),
                        row.get('DESCRIPCIÓN', ''),
                        row.get('CUMPLIDO', ''),
                        fecha_atencion,
                        row.get('OBSERVACIONES', '')
                    ))
                    registros_count += 1
                except Exception as e:
                    print(f"Error insertando fila: {e}")

            print(f"Propagados {registros_count} registros.")

        conn.commit()
        print("✅ Migración completada con éxito.")

    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_data()
