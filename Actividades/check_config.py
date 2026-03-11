import sys
sys.path.insert(0, '.')
from database import obtener_configuracion_usuario

for user in ['admin', 'apoyosistemas']:
    config = obtener_configuracion_usuario(user)
    print(f"User '{user}' config: {config}")
    dc = config.get('datos_contrato', {}) if isinstance(config, dict) else {}
    print(f"  datos_contrato: {dc}")
    print()
