import openpyxl
import os
from config import TEMPLATE_INFORME_FINAL

def diagnose_template():
    if not os.path.exists(TEMPLATE_INFORME_FINAL):
        print(f"Error: Template not found at {TEMPLATE_INFORME_FINAL}")
        return

    wb = openpyxl.load_workbook(TEMPLATE_INFORME_FINAL, data_only=True)
    ws = wb.active
    
    print(f"--- Diagnóstico de Plantilla: {os.path.basename(TEMPLATE_INFORME_FINAL)} ---")
    for row in ws.iter_rows(min_row=1, max_row=20, min_col=1, max_col=10):
        for cell in row:
            if cell.value:
                val = str(cell.value).strip()
                # Mostrar coordenadas y valor para entender la estructura
                print(f"[{cell.coordinate}] -> '{val}'")
                
    print("--- Fin de Diagnóstico ---")

if __name__ == "__main__":
    diagnose_template()
