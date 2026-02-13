import openpyxl
import os

template_path = 'InformeFinal.XLSX'
if not os.path.exists(template_path):
    # Intentar con minúsculas por si acaso
    template_path = 'InformeFinal.xlsx'

if not os.path.exists(template_path):
    print(f"Error: No se encontró la plantilla.")
else:
    print(f"Leyendo: {template_path}")
    wb = openpyxl.load_workbook(template_path)
    ws = wb.active
    print(f"Hoja activa: {ws.title}")
    
    found = False
    for r in range(1, 101):
        for c in range(1, 21):
            val = ws.cell(row=r, column=c).value
            if val is not None:
                print(f"R{r}C{c}: {val}")
                found = True
    
    if not found:
        print("No se encontraron celdas con contenido en el rango R1-100, C1-20.")
