import sys
import os

from templates import (
    LOGIN_TEMPLATE, MAIN_TEMPLATE, GESTION_TEMPLATE, EXPORTAR_TEMPLATE,
    ESTADISTICAS_TEMPLATE, FORMULARIO_REGISTRO, EDIT_REGISTRO_TEMPLATE
)

def test_template(name, template, **kwargs):
    try:
        template.format(**kwargs)
        print(f"✅ {name} OK")
    except Exception as e:
        print(f"❌ {name} ERROR: {e}")

test_template("LOGIN_TEMPLATE", LOGIN_TEMPLATE, error_login="error")
test_template("FORMULARIO_REGISTRO", FORMULARIO_REGISTRO,
            opciones_actividades="", opciones_ubicaciones="",
            opciones_tipos="", opciones_medios="", fecha_hoy="")
test_template("MAIN_TEMPLATE", MAIN_TEMPLATE,
            usuario_actual="u", seccion_registro="s", alertas="a", tabla_registros="t")
test_template("GESTION_TEMPLATE", GESTION_TEMPLATE,
            usuario_actual="u", gestion_actividades="g", gestion_usuarios="u",
            gestion_personal="p", alertas="a", datos_nro="", datos_objeto="",
            datos_nombre="", datos_cedula="", datos_supervisor="")
test_template("ESTADISTICAS_TEMPLATE", ESTADISTICAS_TEMPLATE,
            usuario_actual="u", total_registros=1, total_tipos_actividad=1,
            fecha_min="1", fecha_max="1", promedio_diario="1", data_actividades="[]",
            data_cumplimiento="[]", data_linea="[]", tabla_usuarios_stats="",
            val_fecha_inicio="", val_fecha_fin="")
test_template("EXPORTAR_TEMPLATE", EXPORTAR_TEMPLATE,
            usuario_actual="u", opciones_actividades="", alertas="",
            fecha_min="1", fecha_max="1", total_registros=1,
            total_tipos_actividad=1, ultima_exportacion="", filtro_usuario_html="",
            val_contrato_objeto="", val_contrato_nro="", val_contrato_nombre="",
            val_contrato_cedula="", val_contrato_supervisor="", importar_html="")
test_template("EDIT_REGISTRO_TEMPLATE", EDIT_REGISTRO_TEMPLATE,
            usuario_actual="u", id_reg="1", opciones_actividades="",
            opciones_ubicaciones="", opciones_tipos="", opciones_medios="",
            val_solicitante="", sel_cumplido_si="", sel_cumplido_no="",
            val_fecha_atencion="", val_observaciones="")
