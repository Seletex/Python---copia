import openpyxl
import os

template_path = 'InformeFinal.XLSX'
if not os.path.exists(template_path):
    print(f"Error: {template_path} no existe")
else:
    wb = openpyxl.load_workbook(template_path)
    ws = wb.active
    print(f"Hoja activa: {ws.title}")
    
    print("\n--- Contenido de las primeras 20 filas y 10 columnas ---")
    for r in range(1, 21):
        row_values = []
        for c in range(1, 11):
            val = ws.cell(row=r, column=c).value
            row_values.append(str(val) if val is not None else "")
        if any(v != "" for v in row_values):
            print(f"Fila {r}: {' | '.join(row_values)}")
