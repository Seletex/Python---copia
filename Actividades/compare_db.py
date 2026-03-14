import sqlite3
import os
import json

paths = [
    r"c:\Users\apoyosistemas\Desktop\ACTIVIDADES\actividades.db",
    r"c:\Users\apoyosistemas\Desktop\ACTIVIDADES\Actividades\actividades.db",
    r"c:\Users\apoyosistemas\Desktop\ACTIVIDADES\Actividades\dist\actividades.db"
]

print("--- Comparacion de Bases de Datos ---")
for p in paths:
    if os.path.exists(p):
        try:
            conn = sqlite3.connect(p)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM registros")
            count = cursor.fetchone()[0]
            mtime = os.path.getmtime(p)
            import datetime
            dt = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            print(f"Path: {p}")
            print(f"  Registros: {count}")
            print(f"  Ultima modificacion: {dt}")
            conn.close()
        except Exception as e:
            print(f"Path: {p}")
            print(f"  Error: {e}")
    else:
        print(f"Path: {p}")
        print(f"  [!] No existe")

print("\n--- Variables de Entorno Relevantes ---")
for k, v in os.environ.items():
    if "ACTIVIDADES" in k or "DATA" in k or "PATH" in k[:4]:
        print(f"{k}={v}")
