
import openpyxl
import os

template_path = r'c:\Users\apoyosistemas\Documents\Python - copia\INFORME DE ACTIVIDADES - copia.xlsx'

if os.path.exists(template_path):
    wb = openpyxl.load_workbook(template_path)
    ws = wb.active
    
    print(f"Hoja activa: {ws.title}")
    print("\nCeldas combinadas:")
    for merged_range in ws.merged_cells.ranges:
        print(f" - {merged_range}")
        
    # Inspeccionar las primeras filas para entender el encabezado
    print("\nContenido de las primeras 10 filas:")
    for row in range(1, 11):
        row_data = []
        for col in range(1, 11):
            cell = ws.cell(row=row, column=col)
            row_data.append(str(cell.value))
        print(f"Fila {row}: {' | '.join(row_data)}")
else:
    print(f"No se encontró el archivo en {template_path}")
