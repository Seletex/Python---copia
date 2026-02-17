
import sys
import os
import pandas as pd

# Agregar path
sys.path.append(os.path.join(os.getcwd(), 'Actividades'))

# Importar la nueva implementación
import Actividades.database_sqlite as db

def test_migration():
    print("=== TEST DE MIGRACIÓN SQLITE ===")
    
    # 1. Probar Usuarios
    print("\n1. Cargando Usuarios...")
    users = db.cargar_usuarios()
    print(f"   Usuarios encontrados: {len(users['usuarios'])}")
    print(f"   Ejemplo: {users['usuarios'][:3]}")
    
    # 2. Probar Actividades
    print("\n2. Cargando Actividades Globales...")
    acts = db.cargar_actividades_globales()
    print(f"   Actividades encontradas: {len(acts)}")
    
    # 3. Probar Registros
    print("\n3. Cargando Registros...")
    df = db.cargar_registros()
    print(f"   Registros encontrados: {len(df)}")
    print(f"   Columnas: {df.columns.tolist()}")
    if not df.empty:
        print(f"   Primer registro ID: {df.iloc[0]['ID']}")
        print(f"   Usuario: {df.iloc[0]['USUARIO']}")
        
    # 4. Probar Inserción
    print("\n4. Insertando Nuevo Registro...")
    nuevo_reg = {
        "USUARIO": "admin",
        "TIPO DE ACTIVIDAD": "Prueba SQLite",
        "FECHA": "2023-10-27T10:00",
        "DEPENDENCIA": "Sistemas",
        "SOLICITANTE": "Test Bot",
        "TIPO DE SOLICITUD": "Prueba",
        "MEDIO DE SOLICITUD": "Script",
        "DESCRIPCIÓN": "Test de inserción",
        "CUMPLIDO": "Si",
        "FECHA ATENCIÓN": "2023-10-27T10:30",
        "OBSERVACIONES": "Ninguna"
    }
    
    new_id = db.guardar_registro(nuevo_reg)
    print(f"   Nuevo ID generado: {new_id}")
    
    # Verificar inserción
    df_new = db.cargar_registros()
    print(f"   Registros totales ahora: {len(df_new)}")
    last_reg = df_new[df_new['ID'] == new_id]
    if not last_reg.empty:
        print("   ✅ Registro verificado en DB")
    else:
        print("   ❌ Registro no encontrado")

if __name__ == "__main__":
    test_migration()
