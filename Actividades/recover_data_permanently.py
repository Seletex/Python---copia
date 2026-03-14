import sqlite3
import os

print("--- Iniciando Consolidacion de Datos Permanente ---")

primary_db = r"c:\Users\apoyosistemas\Desktop\ACTIVIDADES\Actividades\actividades.db"
sources = [
    r"c:\Users\apoyosistemas\Desktop\ACTIVIDADES\actividades.db",
    r"c:\Users\apoyosistemas\Desktop\ACTIVIDADES\Actividades\dist\actividades.db"
]

if not os.path.exists(primary_db):
    print(f"[ERROR] La base de datos principal no existe: {primary_db}")
    exit(1)

try:
    conn = sqlite3.connect(primary_db)
    cursor = conn.cursor()
    
    # Asegurar que la tabla existe (por si acaso)
    # Ya la conocemos, pero mejor prevenir
    
    total_recuperados = 0
    
    for src in sources:
        if os.path.exists(src) and os.path.abspath(src) != os.path.abspath(primary_db):
            print(f"Fusionando registros desde: {src}")
            try:
                # Usar ATTACH para copiar registros de forma eficiente
                cursor.execute(f"ATTACH DATABASE '{src}' AS src_db")
                
                # Insertar registros que no existan (comparando por todas las columnas clave excepto ID)
                query = """
                INSERT INTO registros (
                    usuario, tipo_actividad, fecha, dependencia, solicitante, 
                    tipo_solicitud, medio_solicitud, descripcion, cumplido, 
                    fecha_atencion, observaciones
                )
                SELECT 
                    usuario, tipo_actividad, fecha, dependencia, solicitante, 
                    tipo_solicitud, medio_solicitud, descripcion, cumplido, 
                    fecha_atencion, observaciones
                FROM src_db.registros
                WHERE NOT EXISTS (
                    SELECT 1 FROM registros r 
                    WHERE r.usuario = src_db.registros.usuario 
                    AND r.fecha = src_db.registros.fecha
                    AND r.tipo_actividad = src_db.registros.tipo_actividad
                    AND r.descripcion = src_db.registros.descripcion
                )
                """
                cursor.execute(query)
                count = cursor.rowcount
                print(f"  [OK] Registros nuevos fusionados: {count}")
                total_recuperados += count
                
                cursor.execute("DETACH DATABASE src_db")
            except Exception as e:
                print(f"  [ERROR] Fallo al fusionar {src}: {e}")
                try: 
                    cursor.execute("DETACH DATABASE src_db")
                except: 
                    pass
        else:
            print(f"Saltando {src} (no existe o es la misma)")

    conn.commit()
    
    # Verificar total final
    cursor.execute("SELECT COUNT(*) FROM registros")
    final_count = cursor.fetchone()[0]
    print(f"\n--- Resultado Final ---")
    print(f"Total registros en DB principal: {final_count}")
    print(f"Total registros recuperados: {total_recuperados}")
    
    conn.close()
    
except Exception as e:
    print(f"[FATAL ERROR] {e}")
