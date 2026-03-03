import os
import zipfile
import datetime

def zip_project(source_dir, output_filename):
    """Zips the project excluding virtual environments and cache."""
    
    # Archivos/Carpetas a ignorar
    IGNORE = {
        '.venv', 'venv', 'env', 'Lib', 'Scripts', 'Include',  # Entornos virtuales
        '__pycache__', '.git', '.github', '.idea', '.vscode', # Metadatos y temporales
        'logs', 'tmp', 'actividades_deploy.zip',              # Logs y el propio zip
        'target', 'src',                                      # Rust artifacts
        'actividades.db', 'usuarios.json',                    # DATOS: No incluir para no sobreescribir prod
        'config_actividades.json',                            # CONFIG: Respetar la del servidor
        'backups'                                             # Backups locales
    }
    
    files_added = 0
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Modificar dirs in-place para que os.walk no entre en carpetas ignoradas
            dirs[:] = [d for d in dirs if d not in IGNORE]
            
            for file in files:
                if file in IGNORE or file.endswith('.pyc') or file.endswith('.pyo'):
                    continue
                    
                file_path = os.path.join(root, file)
                # Ruta relativa dentro del zip
                arcname = os.path.relpath(file_path, source_dir)
                
                print(f"Agregando: {arcname}")
                zipf.write(file_path, arcname)
                files_added += 1
                
    print(f"\n✅ Zip creado exitosamente: {output_filename}")
    print(f"📦 Total de archivos: {files_added}")

if __name__ == "__main__":
    # Directorio base del proyecto (donde está app.py)
    BASE_DIR = r"c:\Users\apoyosistemas\Documents\Python - copia\Actividades"
    OUTPUT_ZIP = os.path.join(BASE_DIR, "actividades_deploy.zip")
    
    zip_project(BASE_DIR, OUTPUT_ZIP)
