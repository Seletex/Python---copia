
import sys
import os

# Agregar path
sys.path.append(os.path.join(os.getcwd(), 'Actividades'))

try:
    from Actividades.templates import ESTADISTICAS_TEMPLATE
    
    # Intentar formatear con dummy data
    html = ESTADISTICAS_TEMPLATE.format(
        usuario_actual="test",
        total_registros=10,
        total_tipos_actividad=5,
        fecha_min="2023-01-01",
        fecha_max="2023-12-31",
        promedio_diario="1.5",
        data_actividades="{}",
        data_cumplimiento="{}",
        data_linea="{}",
        tabla_usuarios_stats="",
        val_fecha_inicio="",
        val_fecha_fin=""
    )
    print("✅ Template ESTADISTICAS_TEMPLATE is valid.")
except Exception as e:
    print(f"❌ Error in ESTADISTICAS_TEMPLATE: {e}")
except ImportError as e:
    print(f"❌ ImportError: {e}")

