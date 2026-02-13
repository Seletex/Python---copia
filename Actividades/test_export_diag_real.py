import sys
import os
import pandas as pd
from datetime import datetime

# Agregar el directorio actual al path
sys.path.append(os.getcwd())

try:
    from config import TEMPLATE_EXCEL, logger
    from export_service import generar_informe_template, exportar_registros_filtrados
    
    # Simular un DataFrame con las columnas reales que vimos en el archivo
    cols_reales = ['ID', 'TIPO DE ACTIVIDAD', 'FECHA', 'DEPENDENCIA', 'SOLICITANTE', 
                   'TIPO DE SOLICITUD', 'MEDIO DE SOLICITUD', 'DESCRIPCIÓN', 'CUMPLIDO', 
                   'FECHA ATENCIÓN', 'OBSERVACIONES']
    
    # Crear un registro de prueba
    data = {
        'ID': [1],
        'TIPO DE ACTIVIDAD': ['Soporte Técnico'],
        'FECHA': [datetime.now()],
        'DEPENDENCIA': ['Secretaría'],
        'SOLICITANTE': ['Juan Perez'],
        'TIPO DE SOLICITUD': ['Correctivo'],
        'MEDIO DE SOLICITUD': ['Teléfono'],
        'DESCRIPCIÓN': ['Prueba de exportación'],
        'CUMPLIDO': ['Sí'],
        'FECHA ATENCIÓN': [datetime.now().strftime('%Y-%m-%d')],
        'OBSERVACIONES': ['Sin observaciones']
    }
    df = pd.DataFrame(data)
    
    print(f"Columnas del DF de prueba: {df.columns.tolist()}")
    print(f"¿Existe la plantilla?: {os.path.exists(TEMPLATE_EXCEL)}")
    
    output_test = "test_export_real.xlsx"
    print(f"Intentando generar informe en: {output_test}")
    
    # Importar openpyxl para ver si falla ahí
    import openpyxl
    
    success = generar_informe_template(df, output_test)
    if success:
        print("✅ Éxito: El informe se generó correctamente.")
        if os.path.exists(output_test):
            os.remove(output_test)
    else:
        print("❌ Error: generar_informe_template retornó False.")
            
except Exception as e:
    import traceback
    print("❌ Se produjo una excepción durante la prueba:")
    traceback.print_exc()
