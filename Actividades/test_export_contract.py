import sys
import os
import pandas as pd
from datetime import datetime

# Agregar el directorio actual al path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "Actividades"))

try:
    from config import TEMPLATE_EXCEL, logger
    from export_service import generar_informe_template
    
    # Simular registros con dos actividades diferentes para probar subtotales
    data = {
        'USUARIO': ['admin', 'admin', 'admin'],
        'TIPO DE ACTIVIDAD': ['Soporte Técnico', 'Soporte Técnico', 'Mantenimiento'],
        'FECHA': [datetime.now(), datetime.now(), datetime.now()],
        'DEPENDENCIA': ['Secretaría', 'Tesorería', 'Alcaldía'],
        'SOLICITANTE': ['Juan Perez', 'Maria Garcia', 'Carlos Ruiz'],
        'TIPO DE SOLICITUD': ['Correctivo', 'Preventivo', 'Correctivo'],
        'MEDIO DE SOLICITUD': ['Teléfono', 'Email', 'Personal'],
        'CUMPLIDO': ['Sí', 'Sí', 'No'],
        'FECHA ATENCIÓN': [datetime.now().strftime('%Y-%m-%d')] * 3,
        'OBSERVACIONES': ['Prueba 1', 'Prueba 2', 'Prueba 3']
    }
    df = pd.DataFrame(data)
    
    contrato_data = {
        'objeto': 'MANTENIMIENTO DE EQUIPOS DE CÓMPUTO 2024',
        'nro': 'CONTRATO-001',
        'nombre': 'JUAN SEBASTIAN PERDOMO',
        'cedula': '123456789'
    }
    
    output_test = "test_informe_mejorado.xlsx"
    print(f"Intentando generar informe mejorado en: {output_test}")
    
    success = generar_informe_template(df, output_test, contrato_data=contrato_data)
    
    if success:
        print("✅ Éxito: El informe mejorado se generó correctamente.")
        print(f"Archivo generado en: {os.path.abspath(output_test)}")
        # Nota: En este entorno no puedo abrir el Excel, pero si no hubo excepciones, 
        # la lógica de escritura de subtotales y datos de contrato se ejecutó.
    else:
        print("❌ Error: generar_informe_template retornó False.")
            
except Exception as e:
    import traceback
    print("❌ Se produjo una excepción durante la prueba:")
    traceback.print_exc()
