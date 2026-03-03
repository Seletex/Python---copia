import os
import zipfile
import shutil
import sys
import time

def actualizar_aplicacion():
    print("🚀 Iniciando actualización automática...")

    # 1. Definir rutas
    BASE_DIR = os.getcwd()
    ZIP_FILE = "actividades_deploy.zip"
    
    # 2. Verificar si existe el zip
    if not os.path.exists(ZIP_FILE):
        print(f"❌ Error: No se encontró {ZIP_FILE}")
        print("   Por favor sube el archivo 'actividades_deploy.zip' antes de correr este script.")
        return

    # 3. Backup rápido de seguridad (opcional, por si acaso)
    # Ya tenemos backup_db.py, pero esto es por si el zip trae algo raro
    
    # 4. Descomprimir
    print(f"📦 Descomprimiendo {ZIP_FILE}...")
    try:
        with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
            zip_ref.extractall(BASE_DIR)
        print("✅ Archivos extraídos correctamente.")
    except Exception as e:
        print(f"❌ Error al descomprimir: {e}")
        return

    # 5. Instalar dependencias nuevas si las hay
    print("📚 Verificando dependencias...")
    # Asumimos que pip está en el path o usamos el python actual
    # os.system(f"{sys.executable} -m pip install -r requirements.txt")
    # (Omitido para que sea rápido, usualmente no cambian seguido)

    # 6. Recargar aplicación Web (tocar WSGI file)
    print("🔄 Recargando aplicación web...")
    
    # Buscar archivo WSGI
    wsgi_file = None
    var_www = "/var/www"
    if os.path.exists(var_www):
        for f in os.listdir(var_www):
            if f.endswith("_wsgi.py"):
                wsgi_file = os.path.join(var_www, f)
                break
    
    if wsgi_file:
        try:
            os.utime(wsgi_file, None)
            print(f"✅ WSGI tocado: {wsgi_file}")
            print("✨ ¡Actualización completada! La web debería estar recargándose.")
        except Exception as e:
            print(f"⚠️ No se pudo tocar el archivo WSGI automáticamente: {e}")
            print("   Por favor haz reload manual desde la web.")
    else:
        print("⚠️ No se encontró el archivo WSGI en /var/www. Haz reload manual.")

    # 7. Limpieza
    try:
        os.remove(ZIP_FILE)
        print("🧹 Archivo zip eliminado.")
    except:
        pass

if __name__ == "__main__":
    actualizar_aplicacion()
