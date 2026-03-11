
import sqlite3
import pandas as pd
import json
import os
import shutil
from datetime import datetime
from config import (
    CONFIG_FILE, USERS_FILE, EXCEL_FILE, logger, DB_FILE, COLUMNAS
)

def _insert_rows_from_df(cursor, df):
    # Normalizar nombres de columnas
    df.columns = [c.upper().strip() for c in df.columns]
    # Asegurar columnas esperadas para evitar KeyError
    for col in COLUMNAS:
        if col not in df.columns:
            df[col] = ""
    registros_count = 0
    for _, row in df.iterrows():
        try:
            fecha = str(row.get('FECHA', ''))
            fecha_atencion = str(row.get('FECHA ATENCIÓN', ''))
            values = (
                row.get('USUARIO', 'admin'),
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
            )
            # Comprobación de duplicado no destructiva (sin índices únicos)
            cursor.execute('''
                SELECT 1 FROM registros
                WHERE usuario=? AND tipo_actividad=? AND fecha=? AND dependencia=? AND solicitante=?
                  AND tipo_solicitud=? AND medio_solicitud=? AND descripcion=? AND cumplido=?
                  AND fecha_atencion=? AND observaciones=?
                LIMIT 1
            ''', values)
            if cursor.fetchone():
                continue
            cursor.execute('''
                INSERT INTO registros (
                    usuario, tipo_actividad, fecha, dependencia, solicitante,
                    tipo_solicitud, medio_solicitud, descripcion, cumplido,
                    fecha_atencion, observaciones
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', values)
            registros_count += 1
        except Exception as e:
            print(f"Error insertando fila: {e}")
    return registros_count

def import_from_excel(excel_path):
    if not os.path.exists(DB_FILE):
        raise RuntimeError(f"La base de datos {DB_FILE} no existe.")
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"No se encontró el archivo: {excel_path}")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        # Respaldo previo no destructivo
        try:
            backup_dir = os.path.join(os.path.dirname(DB_FILE), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"actividades_{ts}.db")
            shutil.copy2(DB_FILE, backup_path)
            print(f"Backup creado: {backup_path}")
        except Exception as _e:
            print(f"Advertencia: no se pudo crear backup previo ({_e}). Continuando...")
        df = pd.read_excel(excel_path, engine='openpyxl')
        count = _insert_rows_from_df(cursor, df)
        conn.commit()
        print(f"✅ Importación desde {excel_path} completada. Agregadas {count} filas.")
        return count
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()

def migrate_data():
    if not os.path.exists(DB_FILE):
        print(f"Error: La base de datos {DB_FILE} no existe. Ejecuta database_setup.py primero.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Respaldo previo no destructivo
        try:
            backup_dir = os.path.join(os.path.dirname(DB_FILE), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"actividades_{ts}.db")
            shutil.copy2(DB_FILE, backup_path)
            print(f"Backup creado: {backup_path}")
        except Exception as _e:
            print(f"Advertencia: no se pudo crear backup previo ({_e}). Continuando...")

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
            registros_count = _insert_rows_from_df(cursor, df)
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
