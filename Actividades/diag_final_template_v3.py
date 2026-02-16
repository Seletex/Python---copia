
import openpyxl
import os
from Actividades.config import TEMPLATE_INFORME_FINAL

if os.path.exists(TEMPLATE_INFORME_FINAL):
    print(f"Inspeccionando: {TEMPLATE_INFORME_FINAL}")
    wb = openpyxl.load_workbook(TEMPLATE_INFORME_FINAL)
    ws = wb.active
    
    print(f"Hoja activa: {ws.title}")
    print("\nCeldas combinadas:")
    ranges = sorted(list(ws.merged_cells.ranges), key=lambda r: r.min_row)
    for merged_range in ranges:
        if merged_range.min_row < 15: # Solo mostrar las primeras
            print(f" - {merged_range}")
        
    print("\nContenido de las primeras 15 filas:")
    for row in range(1, 16):
        row_data = []
        for col in range(1, 11):
            cell = ws.cell(row=row, column=col)
            row_data.append(str(cell.value) if cell.value is not None else "")
        print(f"Fila {row}: {' | '.join(row_data)}")
else:
    print(f"No se encontró el archivo en {TEMPLATE_INFORME_FINAL}")
