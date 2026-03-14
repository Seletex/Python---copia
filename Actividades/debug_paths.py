from config import DATA_DIR, MASTER_DIR, DB_FILE, EXCEL_FILE, DIRS_SEARCH
import os

print(f"--- Configuracion de Rutas ---")
print(f"DATA_DIR: {DATA_DIR}")
print(f"MASTER_DIR: {MASTER_DIR}")
print(f"DB_FILE: {DB_FILE}")
print(f"EXCEL_FILE: {EXCEL_FILE}")
print(f"DIRS_SEARCH: {DIRS_SEARCH}")

if MASTER_DIR:
    print(f"\nEstado de MASTER_DIR ({MASTER_DIR}):")
    if os.path.exists(MASTER_DIR):
        print(f"  [OK] Existe")
        try:
            test_file = os.path.join(MASTER_DIR, ".write_test")
            with open(test_file, "w") as f: f.write("test")
            os.remove(test_file)
            print(f"  [OK] Es escribible")
        except Exception as e:
            print(f"  [ERROR] No es escribible: {e}")
        
        print(f"  Contenido del directorio:")
        try:
            for f in os.listdir(MASTER_DIR):
                if f.endswith(('.db', '.xlsx', '.json')):
                    size = os.path.getsize(os.path.join(MASTER_DIR, f)) / 1024
                    print(f"    - {f} ({size:.2f} KB)")
        except Exception as e:
            print(f"    Error listando: {e}")
    else:
        print(f"  [ERROR] NO existe")
else:
    print(f"\n[!] No hay MASTER_DIR configurado. La aplicacion esta operando de forma 100% local.")
