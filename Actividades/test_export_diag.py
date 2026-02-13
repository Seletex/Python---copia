import sys
import os
import pandas as pd
from datetime import datetime

# Agregar el directorio actual al path
sys.path.append(os.getcwd())

try:
    from config import TEMPLATE_EXCEL, logger
    from export_service import generar_informe_template, exportar_registros_filtrados
    
    print(f"Plantilla configurada: {TEMPLATE_EXCEL}")
    print(f"¿Existe la plantilla?: {os.path.exists(TEMPLATE_EXCEL)}")
    
    # Cargar registros de prueba (usuario admin)
    print("Cargando registros para admin...")
    df, stats = exportar_registros_filtrados(usuario='admin')
    
    if df.empty:
        print("Error: No hay registros para el usuario 'admin'. Por favor agregue uno o use otro usuario.")
    else:
        print(f"Registros encontrados: {len(df)}")
        output_test = "test_export.xlsx"
        print(f"Intentando generar informe en: {output_test}")
        
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
