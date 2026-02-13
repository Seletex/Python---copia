import sys
import os
import pandas as pd
from datetime import datetime

# Agregar el directorio actual al path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "Actividades"))

try:
    from export_final_service import generar_informe_final_resumen
    
    # Simular registros para el resumen
    data = {
        'TIPO DE ACTIVIDAD': [
            'Soporte Técnico', 'Soporte Técnico', 
            'Mantenimiento', 'Mantenimiento', 'Mantenimiento',
            'Capacitación'
        ],
        'FECHA': [datetime.now()] * 6,
        'USUARIO': ['admin'] * 6
    }
    df = pd.DataFrame(data)
    
    contrato_data = {
        'objeto': 'CONTRATO DE PRUEBA FINAL',
        'nro': '2024-FINAL-001',
        'nombre': 'JUAN PRUEBA',
        'cedula': '999999',
        'supervisor': 'SUPERVISOR PRUEBA'
    }
    
    output_test = "test_informe_final.xlsx"
    print(f"Generando Informe Final en: {output_test}")
    
    success = generar_informe_final_resumen(df, output_test, contrato_data=contrato_data)
    
    if success:
        print("✅ Éxito: El Informe Final se generó correctamente.")
        print(f"Archivo guardado en: {os.path.abspath(output_test)}")
    else:
        print("❌ Error: generar_informe_final_resumen retornó False.")
            
except Exception as e:
    import traceback
    print("❌ Excepción:")
    traceback.print_exc()
