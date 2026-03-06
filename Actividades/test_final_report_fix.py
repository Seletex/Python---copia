import sys
import os
import pandas as pd
from datetime import datetime
import openpyxl

# Agregar el directorio actual al path
sys.path.append(os.getcwd())

try:
    from config import TEMPLATE_INFORME_FINAL
    from export_final_service import generar_informe_final_resumen
    
    # Simular registros
    data = {
        'TIPO DE ACTIVIDAD': ['Soporte Técnico', 'Soporte Técnico', 'Mantenimiento'],
        'FECHA': [datetime.now()] * 3
    }
    df = pd.DataFrame(data)
    
    contrato_data = {
        'nro': '123-2026',
        'objeto': 'Prestación de servicios de apoyo a la oficina de sistemas',
        'nombre': 'ALEJANDRO PRUEBA',
        'cedula': '10203040',
        'supervisor': 'SUPERVISOR DE PRUEBA'
    }
    
    output_test = "test_final_report_output_v2.xlsx"
    print(f"Generando informe final de prueba en: {output_test}")
    
    success = generar_informe_final_resumen(df, output_test, contrato_data=contrato_data)
    
    if success and os.path.exists(output_test):
        wb = openpyxl.load_workbook(output_test)
        ws = wb.active
        
        print("\nVerificando contenido:")
        checks = [
            ("C2", contrato_data['nro']),
            ("C3", contrato_data['objeto']),
            ("C4", contrato_data['nombre']),
            ("C5", contrato_data['cedula']),
            ("B9", contrato_data['nombre']), # Elaborado
            ("B11", contrato_data['supervisor']), # Vo Bo
            ("B12", contrato_data['supervisor'])  # Supervisor contrato
        ]
        
        any_error = False
        for coord, expected in checks:
            val = str(ws[coord].value or "").upper()
            if expected.upper() in val:
                print(f" - OK: Encontrado '{expected}' en {coord}")
            else:
                print(f" - ERROR: No se encontró '{expected}' en {coord}. Valor actual: '{val}'")
                any_error = True

        # Verificando fusiones de celdas (Ancho Col 10)
        print("\nVerificando fusiones de celdas (Ancho Col 10):")
        ranges = ws.merged_cells.ranges
        j_merges = 0
        for r in sorted(list(ranges), key=lambda x: x.min_row):
            if r.max_col == 10:
                print(f" - Fila {r.min_row:02d}: {r}")
                j_merges += 1
        
        if not any_error and j_merges > 0:
            print("\nOK: Se encontraron todos los datos y las fusiones de ancho total.")
        else:
            print(f"\nADVERTENCIA: any_error={any_error}, j_merges={j_merges}")
            
    else:
        print("Error: No se pudo generar el archivo de salida.")
            
except Exception as e:
    import traceback
    traceback.print_exc()
