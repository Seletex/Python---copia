
import openpyxl
import os

template_path = r'c:\Users\apoyosistemas\Documents\Python - copia\INFORME DE ACTIVIDADES - copia.xlsx'

if os.path.exists(template_path):
    wb = openpyxl.load_workbook(template_path)
    ws = wb.active
    
    print(f"Hoja activa: {ws.title}")
    
    # Inspeccionar estilos de la fila 8
    print("\nEstilos de la fila 8:")
    for col in range(1, 10):
        cell = ws.cell(row=8, column=col)
        print(f"Col {col}: Border={cell.border}, Alignment={cell.alignment}, Font={cell.font}")
else:
    print(f"No se encontró el archivo")
