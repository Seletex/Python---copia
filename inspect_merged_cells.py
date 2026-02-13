
import openpyxl

template_path = r"c:\Users\apoyosistemas\Documents\Python - copia\INFORME DE ACTIVIDADES - copia.xlsx"

try:
    wb = openpyxl.load_workbook(template_path)
    ws = wb.active
    print(f"Sheet: {ws.title}")
    
    merged_ranges = list(ws.merged_cells.ranges)
    merged_ranges.sort(key=lambda r: r.min_row)
    
    print(f"Total merged ranges: {len(merged_ranges)}")
    for merged_range in merged_ranges:
        print(f"Range: {merged_range}")
        
except Exception as e:
    print(f"Error: {e}")
