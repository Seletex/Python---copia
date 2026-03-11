import sqlite3
import os

db_file = r"\\sistema2021\H\Sistemas\ACTIVIDADES\Actividades\actividades.db"
if os.path.exists(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM listas_globales WHERE tipo = 'actividad'")
    rows = cursor.fetchall()
    print("Actividades Globales en DB:")
    for row in rows:
        print(f"- {row[0]}")
    conn.close()
else:
    print("Archivo de base de datos no encontrado")
