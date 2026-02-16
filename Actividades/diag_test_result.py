
import openpyxl
import os

path = "test_informe_final.xlsx"
if os.path.exists(path):
    print(f"Inspeccionando resultado: {path}")
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    
    print("\nCeldas combinadas en el resultado:")
    ranges = sorted(list(ws.merged_cells.ranges), key=lambda r: r.min_row)
    for merged_range in ranges:
        if merged_range.min_row >= 7:
            print(f" - {merged_range}")
            
    print("\nContenido de las filas de datos (7 en adelante):")
    for row in range(7, 15):
        row_data = []
        for col in [1, 8]: # Columnas A y H que son las bases de las combinadas
            cell = ws.cell(row=row, column=col)
            val = cell.value if cell.value is not None else ""
            row_data.append(f"Col {col}: '{val}'")
        print(f"Fila {row}: {' | '.join(row_data)}")
else:
    print(f"No se encontró el archivo {path}")
