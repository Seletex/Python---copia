import os
import pandas as pd
import openpyxl
import copy
from datetime import datetime
from config import TEMPLATE_INFORME_FINAL, logger
from utils import medir_tiempo

@medir_tiempo
def generar_informe_final_resumen(df, output_path, contrato_data=None):
    """
    Genera un informe concentrado contando actividades por tipo.
    Mantiene los encabezados institucionales de la plantilla.
    """
    try:
        logger.info(f"Generando Informe Final Concentrado. Registros: {len(df)}")
        if not os.path.exists(TEMPLATE_INFORME_FINAL):
            logger.error(f"Plantilla no encontrada: {TEMPLATE_INFORME_FINAL}")
            return False

        wb = openpyxl.load_workbook(TEMPLATE_INFORME_FINAL)
        ws = wb.active
        
        # 1. Agrupar y contar actividades
        if 'TIPO DE ACTIVIDAD' in df.columns:
            resumen = df['TIPO DE ACTIVIDAD'].value_counts().reset_index()
            resumen.columns = ['Actividad', 'Cantidad']
        else:
            resumen = pd.DataFrame(columns=['Actividad', 'Cantidad'])

        # 2. Encabezados Institucionales (misma lógica que el detallado)
        if contrato_data:
            if contrato_data.get('nro'):
                ws.cell(row=2, column=3, value=contrato_data['nro'].upper())
            if contrato_data.get('objeto'):
                ws.cell(row=3, column=3, value=contrato_data['objeto'].upper())
            
            nombre_contratista = contrato_data.get('nombre', '').upper()
            if not nombre_contratista:
                usuarios = df['USUARIO'].unique() if 'USUARIO' in df.columns else []
                nombre_contratista = usuarios[0].upper() if len(usuarios) == 1 else "VARIOS"
            ws.cell(row=4, column=3, value=nombre_contratista)
            
            if contrato_data.get('cedula'):
                ws.cell(row=5, column=3, value=contrato_data['cedula'])

        # Rango de fechas (Fila 6)
        if not df.empty and 'FECHA' in df.columns:
            fechas_dt = pd.to_datetime(df['FECHA'], errors='coerce').dropna()
            if not fechas_dt.empty:
                ws.cell(row=6, column=3,
                        value=f"{fechas_dt.min().strftime('%d/%m/%Y')} al {fechas_dt.max().strftime('%d/%m/%Y')}")

        # 3. Limpieza de área de datos (Filas 8 en adelante)
        for row_idx in range(8, 200):
            for col_idx in range(1, 11):
                ws.cell(row=row_idx, column=col_idx, value=None)
        
        # Desenlazar celdas desde la fila 8 en adelante
        merged_ranges = list(ws.merged_cells.ranges)
        for merged_range in merged_ranges:
            if merged_range.min_row >= 8:
                try:
                    ws.unmerge_cells(str(merged_range))
                except Exception: pass

        # 4. Escribir Tabla de Resumen
        current_row = 8
        ws.cell(row=current_row, column=1, value="RESUMEN DE ACTIVIDADES REALIZADAS:").font = openpyxl.styles.Font(bold=True)
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=8)
        current_row += 2
        
        ws.cell(row=current_row, column=1, value="DESCRIPCIÓN DE LA ACTIVIDAD").font = openpyxl.styles.Font(bold=True)
        ws.cell(row=current_row, column=9, value="CONTEO").font = openpyxl.styles.Font(bold=True)
        # Aplicar borde a cabecera de tabla
        for c in range(1, 10):
            ws.cell(row=current_row, column=c).border = openpyxl.styles.Border(
                left=openpyxl.styles.Side(style='thin'),
                right=openpyxl.styles.Side(style='thin'),
                top=openpyxl.styles.Side(style='thin'),
                bottom=openpyxl.styles.Side(style='thin')
            )
        current_row += 1
        
        for _, r in resumen.iterrows():
            ws.cell(row=current_row, column=1, value=r['Actividad'])
            ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=8)
            ws.cell(row=current_row, column=9, value=r['Cantidad'])
            
            # Bordes para la fila
            for c in range(1, 10):
                ws.cell(row=current_row, column=c).border = openpyxl.styles.Border(
                    left=openpyxl.styles.Side(style='thin'),
                    right=openpyxl.styles.Side(style='thin'),
                    top=openpyxl.styles.Side(style='thin'),
                    bottom=openpyxl.styles.Side(style='thin')
                )
            current_row += 1
            
        # Total General
        ws.cell(row=current_row, column=1, value="TOTAL GENERAL DE ACTIVIDADES:").font = openpyxl.styles.Font(bold=True)
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=8)
        ws.cell(row=current_row, column=9, value=resumen['Cantidad'].sum()).font = openpyxl.styles.Font(bold=True)
        for c in range(1, 10):
            ws.cell(row=current_row, column=c).border = openpyxl.styles.Border(
                left=openpyxl.styles.Side(style='thin'),
                right=openpyxl.styles.Side(style='thin'),
                top=openpyxl.styles.Side(style='thin'),
                bottom=openpyxl.styles.Side(style='thin')
            )
        current_row += 2
        
        # 5. Fecha e Informe (mismo estilo que el detallado)
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        ahora = datetime.now()
        ws.cell(row=current_row, column=1, value="Fecha de informe:").font = openpyxl.styles.Font(bold=True)
        ws.cell(row=current_row, column=2, value=f"{meses[ahora.month-1]} de {ahora.year}")
        ws.merge_cells(start_row=current_row, start_column=2, end_row=current_row, end_column=8)
        current_row += 1
        
        # Firmas
        if contrato_data:
            if contrato_data.get('nombre'):
                ws.cell(row=current_row, column=1, value="Elaborado por:").font = openpyxl.styles.Font(bold=True)
                ws.cell(row=current_row, column=2, value=contrato_data['nombre'].upper())
                ws.merge_cells(start_row=current_row, start_column=2, end_row=current_row, end_column=8)
                current_row += 1
                ws.cell(row=current_row, column=1, value="CONTRATISTA:").font = openpyxl.styles.Font(bold=True)
                ws.merge_cells(start_row=current_row, start_column=2, end_row=current_row, end_column=8)
                current_row += 1                
            
            if contrato_data.get('supervisor'):
                ws.cell(row=current_row, column=1, value="Vo.Bo:").font = openpyxl.styles.Font(bold=True)
                ws.cell(row=current_row, column=2, value=contrato_data['supervisor'].upper())
                ws.merge_cells(start_row=current_row, start_column=2, end_row=current_row, end_column=8)
                current_row += 1
                ws.cell(row=current_row, column=1, value="SUPERVISOR:").font = openpyxl.styles.Font(bold=True)
                ws.merge_cells(start_row=current_row, start_column=2, end_row=current_row, end_column=8)
                current_row += 1

        wb.save(output_path)
        return True
    except Exception as e:
        logger.error(f"Error generando informe final: {e}")
        return False
