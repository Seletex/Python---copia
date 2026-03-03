import shutil
import os
import datetime
from config import DB_FILE, BASE_DIR

def backup_database():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(BASE_DIR, "backups")
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
    backup_file = os.path.join(backup_dir, f"actividades_{timestamp}.db")
    
    if os.path.exists(DB_FILE):
        try:
            shutil.copy2(DB_FILE, backup_file)
            print(f"✅ Backup creado exitosamente: {backup_file}")
            
            # Limpiar backups viejos (mantener últimos 5)
            backups = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.endswith('.db')])
            if len(backups) > 5:
                for old_backup in backups[:-5]:
                    os.remove(old_backup)
                    print(f"🗑️ Backup antiguo eliminado: {old_backup}")
                    
        except Exception as e:
            print(f"❌ Error creando backup: {e}")
    else:
        print("⚠️ No se encontró la base de datos para hacer backup.")

if __name__ == "__main__":
    backup_database()
