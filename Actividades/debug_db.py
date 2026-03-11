import sqlite3
import pandas as pd

try:
    conn = sqlite3.connect(r'c:\Users\apoyosistemas\Desktop\ACTIVIDADES\actividades.db')
    cursor = conn.cursor()
    cursor.execute("SELECT descripcion, observaciones, tipo_actividad FROM registros ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    
    with open('debug_output.txt', 'w', encoding='utf-8') as f:
        f.write("Primeros 5 registros en DB directamente:\n")
        cursor.execute("SELECT id, descripcion, observaciones, tipo_actividad FROM registros ORDER BY id ASC LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            f.write(str(row) + "\n")
            
        df = pd.read_sql_query("SELECT id, descripcion, observaciones, tipo_actividad FROM registros ORDER BY id ASC LIMIT 5", conn)
        f.write("\nPrimeros 5 registros con Pandas:\n")
        f.write(df.to_string())
    conn.close()
except Exception as e:
    print("Error:", e)
