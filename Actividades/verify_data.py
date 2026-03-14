import sqlite3
import os
import pandas as pd
from config import DB_FILE, EXCEL_FILE, logger

def verify_data():
    print(f"--- Diagnostico de Datos ---")
    print(f"Archivo de Base de Datos: {DB_FILE}")
    print(f"Archivo Excel de Respaldo: {EXCEL_FILE}")
    
    # 1. Verificar existencia de archivos
    if os.path.exists(DB_FILE):
        size = os.path.getsize(DB_FILE) / 1024
        print(f"[OK] La base de datos existe ({size:.2f} KB)")
    else:
        print(f"[ERROR] La base de datos NO se encuentra en la ruta esperada.")

    if os.path.exists(EXCEL_FILE):
        size = os.path.getsize(EXCEL_FILE) / 1024
        print(f"[OK] El archivo Excel existe ({size:.2f} KB)")
    else:
        print(f"[!] El archivo Excel no existe o no se ha sincronizado aun.")

    # 2. Consultar registros en SQLite
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM registros")
        total = cursor.fetchone()['total']
        print(f"\nTotal de registros en BD: {total}")
        
        if total > 0:
            print("\nUltimos 5 registros guardados:")
            cursor.execute("SELECT id, usuario, fecha, tipo_actividad FROM registros ORDER BY id DESC LIMIT 5")
            rows = cursor.fetchall()
            for row in rows:
                print(f"  ID: {row['id']} | Usuario: {row['usuario']} | Fecha: {row['fecha']} | Actividad: {row['tipo_actividad'][:50]}...")
        
        conn.close()
    except Exception as e:
        print(f"[ERROR] Al consultar la base de datos: {e}")

    # 3. Verificar sincronizacion con Excel
    try:
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE)
            print(f"\nTotal de registros en Excel: {len(df)}")
            if len(df) != total:
                print(f"[!] Alerta: El numero de registros en Excel ({len(df)}) no coincide con la BD ({total}).")
            else:
                print(f"[OK] Sincronizacion BD-Excel: Correcta.")
    except Exception as e:
        print(f"[!] Error al leer el Excel: {e}")

if __name__ == "__main__":
    verify_data()
