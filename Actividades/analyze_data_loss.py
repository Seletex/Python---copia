import sqlite3
import os
import pandas as pd

paths = [
    r"c:\Users\apoyosistemas\Desktop\ACTIVIDADES\actividades.db",
    r"c:\Users\apoyosistemas\Desktop\ACTIVIDADES\Actividades\actividades.db",
    r"c:\Users\apoyosistemas\Desktop\ACTIVIDADES\Actividades\dist\actividades.db"
]

all_dfs = []

print("--- Resumen de Contenidos ---")
for p in paths:
    if os.path.exists(p):
        try:
            conn = sqlite3.connect(p)
            df = pd.read_sql_query("SELECT * FROM registros", conn)
            # Normalizar para comparacion
            df['source_file'] = os.path.basename(p)
            df['source_path'] = p
            all_dfs.append(df)
            print(f"File: {p}")
            print(f"  Registros: {len(df)}")
            if not df.empty:
                print(f"  Usuarios: {df['usuario'].unique()}")
                print(f"  Rango Fechas: {df['fecha'].min()} a {df['fecha'].max()}")
            conn.close()
        except Exception as e:
            print(f"Error en {p}: {e}")

if all_dfs:
    combined = pd.concat(all_dfs, ignore_index=True)
    # Identificar registros únicos basados en columnas clave (evitando el ID que puede variar)
    cols_to_check = ['usuario', 'tipo_actividad', 'fecha', 'dependencia', 'solicitante', 'descripcion']
    # Asegurar que las columnas existen en el df
    cols_present = [c for c in cols_to_check if c in combined.columns]
    
    unique_records = combined.drop_duplicates(subset=cols_present)
    print(f"\n--- Consolidacion ---")
    print(f"Total registros (con duplicados): {len(combined)}")
    print(f"Total registros UNICOS: {len(unique_records)}")
    
    print("\nRegistros por usuario en el conjunto consolidado:")
    print(unique_records['usuario'].value_counts())
    
    # Mostrar algunos registros unicos que podrian faltar en la DB principal
    main_db_path = r"c:\Users\apoyosistemas\Desktop\ACTIVIDADES\Actividades\actividades.db"
    main_df = next((df for df in all_dfs if df['source_path'].iloc[0] == main_db_path), pd.DataFrame())
    
    if not main_df.empty:
        missing = unique_records[~unique_records.set_index(cols_present).index.isin(main_df.set_index(cols_present).index)]
        if not missing.empty:
            print(f"\n[!] Se han encontrado {len(missing)} registros que NO estan en la base de datos principal.")
            print("Ejemplos de registros faltantes:")
            print(missing[['usuario', 'fecha', 'tipo_actividad']].head())
            
            # Guardar backup consolidado
            unique_records.to_csv("consolidado_temp.csv", index=False)
            print(f"\nSe ha guardado un archivo 'consolidado_temp.csv' con todos los registros unicos encontrados.")
