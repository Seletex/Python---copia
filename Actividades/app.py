
from flask import Flask, request, redirect, url_for, session, render_template_string, send_file, make_response
import os
import json
from datetime import datetime
from functools import wraps

# Importar módulos existentes
from config import logger, ACTIVIDADES_DEFAULT
from database import (
    cargar_usuarios, guardar_usuarios,
    cargar_actividades, cargar_actividades_globales, guardar_actividades,
    cargar_ubicaciones, guardar_ubicaciones,
    cargar_tipos_solicitud, guardar_tipos_solicitud,
    cargar_medios_solicitud, guardar_medios_solicitud,
    cargar_registros, guardar_registro, eliminar_registro, actualizar_registro,
    obtener_configuracion_usuario, guardar_configuracion_usuario
)
from activity_service import agregar_actividad_personal, eliminar_actividad_personal
from export_service import (
    exportar_registros_filtrados, obtener_estadisticas_exportacion,
    generar_informe_template
)
from html_utils import (
    generar_opciones_actividades, generar_opciones_ubicaciones,
    generar_opciones_tipos_solicitud, generar_opciones_medios_solicitud,
    generar_opciones_usuarios, generar_gestion_usuarios,
    generar_gestion_actividades_globales, generar_gestion_actividades_personales,
    generar_gestion_ubicaciones, generar_gestion_tipos_solicitud,
    generar_gestion_medios_solicitud, generar_tabla_registros_recientes
)
from templates import (
    LOGIN_TEMPLATE, MAIN_TEMPLATE, GESTION_TEMPLATE,
    EXPORTAR_TEMPLATE, ESTADISTICAS_TEMPLATE
)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))

# =============================================================================
# DECORADORES
# =============================================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('index', error='No autorizado'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session or session['usuario'] != 'admin':
            return redirect(url_for('gestion', error='Acceso denegado'))
        return f(*args, **kwargs)
    return decorated_function

# =============================================================================
# RUTAS PRINCIPALES
# =============================================================================

@app.route('/', methods=['GET', 'POST'])
def index():
    usuario_actual = session.get('usuario')
    
    # GET: Mostrar página
    if request.method == 'GET':
        if not usuario_actual:
            error_msg = ""
            if request.args.get('error'):
                error_msg = '<div class="alert alert-danger">Usuario no encontrado</div>'
            return render_template_string(LOGIN_TEMPLATE.format(error_login=error_msg))
        
        # Alertas
        alertas = ""
        if request.args.get('success'):
            alertas = '<div class="alert alert-success alert-dismissible fade show">✅ Registro guardado<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
        elif request.args.get('deleted'):
            alertas = '<div class="alert alert-info alert-dismissible fade show">🗑️ Registro eliminado<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
        
        # Cargar datos
        df = cargar_registros(usuario_actual)
        tabla_html = generar_tabla_registros_recientes(df, usuario_actual)
        
        return render_template_string(MAIN_TEMPLATE.format(
            usuario_actual=usuario_actual,
            opciones_actividades=generar_opciones_actividades(usuario_actual),
            opciones_ubicaciones=generar_opciones_ubicaciones(),
            opciones_tipos=generar_opciones_tipos_solicitud(),
            opciones_medios=generar_opciones_medios_solicitud(),
            alertas=alertas,
            fecha_hoy=datetime.now().strftime('%Y-%m-%d'),
            tabla_registros=tabla_html
        ))

    if request.method == 'POST':
        usuario = session.get('usuario')
        if not usuario:
            # Login primero
            usuario = request.form.get('usuario', '').strip()
            # ... validación login ...
            return redirect(url_for('index'))
            
        data = {
            "USUARIO": usuario_actual,
            "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "TIPO DE ACTIVIDAD": request.form.get('actividad'),
            "DEPENDENCIA": request.form.get('ubicacion'), # Antes era dependencia, ahora ubicacion en UI
            "SOLICITANTE": request.form.get('solicitante'),
            "TIPO DE SOLICITUD": request.form.get('tipo_solicitud'),
            "MEDIO DE SOLICITUD": request.form.get('medio_solicitud'),
            "DESCRIPCIÓN": request.form.get('descripcion'),
            "CUMPLIDO": request.form.get('cumplido'),
            "FECHA ATENCIÓN": request.form.get('fecha_atencion'),
            "OBSERVACIONES": request.form.get('observaciones')
        }
        
        if guardar_registro(data):
            return redirect(url_for('index', success=1))
        else:
            return redirect(url_for('index', error=1))

@app.route('/login', methods=['POST'])
def login():
    usuario = request.form.get('usuario', '').strip()
    if usuario:
        usuarios_data = cargar_usuarios()
        usuarios = usuarios_data.get("usuarios", [])
        # Búsqueda case-insensitive
        encontrado = next((u for u in usuarios if u.lower() == usuario.lower()), None)
        
        if encontrado:
            session['usuario'] = encontrado
            # Cookie permanente (opcional, Flask sessions son firmadas)
            session.permanent = True 
            return redirect(url_for('index'))
            
    return redirect(url_for('index', error=1))

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('index'))

# =============================================================================
# RUTAS DE GESTIÓN
# =============================================================================

@app.route('/gestion')
def gestion():
    usuario_actual = session.get('usuario')
    if not usuario_actual:
        return redirect(url_for('index'))
    
    alertas = ""
    if request.args.get('msg'):
        msg = request.args.get('msg')
        alertas = f'<div class="alert alert-success alert-dismissible fade show">✅ {msg}<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
    elif request.args.get('error'):
        alertas = '<div class="alert alert-danger alert-dismissible fade show">❌ Error en la operación<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
    
    # Generar componentes de gestión según rol
    es_admin = usuario_actual == "admin"
    
    gestion_actividades = generar_gestion_actividades_globales() if es_admin else ""
    gestion_usuarios = generar_gestion_usuarios(usuario_actual) if es_admin else ""
    gestion_ubicaciones = generar_gestion_ubicaciones() if es_admin else ""
    gestion_tipos = generar_gestion_tipos_solicitud() if es_admin else ""
    gestion_medios = generar_gestion_medios_solicitud() if es_admin else ""
    gestion_personal = generar_gestion_actividades_personales(usuario_actual)
    
    return render_template_string(GESTION_TEMPLATE.format(
        usuario_actual=usuario_actual,
        gestion_actividades=f"{gestion_actividades}{gestion_ubicaciones}{gestion_tipos}{gestion_medios}",
        gestion_usuarios=gestion_usuarios,
        gestion_personal=gestion_personal,
        alertas=alertas
    ))

# --- ACCIONES ADMINISTRATIVAS ---

@app.route('/agregar_usuario', methods=['POST'])
def agregar_usuario():
    if session.get('usuario') != 'admin':
        return redirect(url_for('gestion', error='No autorizado'))
        
    nuevo_usuario = request.form.get('nuevo_usuario', '').strip()
    if nuevo_usuario:
        usuarios_data = cargar_usuarios()
        usuarios = usuarios_data.get("usuarios", [])
        if nuevo_usuario not in usuarios:
            usuarios.append(nuevo_usuario)
            usuarios_data["usuarios"] = usuarios
            guardar_usuarios(usuarios_data)
            return redirect(url_for('gestion', msg='Usuario agregado'))
            
    return redirect(url_for('gestion', error='Error al agregar usuario'))

@app.route('/eliminar_usuario', methods=['POST'])
def eliminar_usuario():
    if session.get('usuario') != 'admin':
        return redirect(url_for('gestion', error='No autorizado'))
        
    usuario = request.form.get('usuario', '').strip()
    if usuario and usuario != 'admin':
        usuarios_data = cargar_usuarios()
        if usuario in usuarios_data.get("usuarios", []):
            usuarios_data["usuarios"].remove(usuario)
            guardar_usuarios(usuarios_data)
            return redirect(url_for('gestion', msg='Usuario eliminado'))
            
    return redirect(url_for('gestion', error='Error al eliminar usuario'))

# --- GESTIÓN DE LISTAS (Generic handlers mapped) ---

@app.route('/agregar_actividad_global', methods=['POST'])
def agregar_actividad_global():
    if session.get('usuario') != 'admin': return redirect(url_for('gestion'))
    item = request.form.get('nuevo_item', '').strip()
    if item:
        act = cargar_actividades_globales()
        if item not in act:
            act.append(item)
            guardar_actividades(act)
    return redirect(url_for('gestion', msg='Actividad agregada'))

@app.route('/eliminar_actividad_global', methods=['POST'])
def eliminar_actividad_global():
    if session.get('usuario') != 'admin': return redirect(url_for('gestion'))
    item = request.form.get('actividad', '').strip()
    if item:
        act = cargar_actividades_globales()
        if item in act:
            act.remove(item)
            guardar_actividades(act)
    return redirect(url_for('gestion', msg='Actividad eliminada'))

@app.route('/agregar_ubicacion', methods=['POST'])
def agregar_ubicacion():
    if session.get('usuario') != 'admin': return redirect(url_for('gestion'))
    item = request.form.get('nuevo_item', '').strip()
    if item:
        lista = cargar_ubicaciones()
        if item not in lista:
            lista.append(item)
            guardar_ubicaciones(lista)
    return redirect(url_for('gestion', msg='Ubicación agregada'))

@app.route('/eliminar_ubicacion', methods=['POST'])
def eliminar_ubicacion():
    if session.get('usuario') != 'admin': return redirect(url_for('gestion'))
    item = request.form.get('ubicacion', '').strip()
    if item:
        lista = cargar_ubicaciones()
        if item in lista:
            lista.remove(item)
            guardar_ubicaciones(lista)
    return redirect(url_for('gestion', msg='Ubicación eliminada'))

@app.route('/agregar_tipo_solicitud', methods=['POST'])
def agregar_tipo_solicitud():
    if session.get('usuario') != 'admin': return redirect(url_for('gestion'))
    item = request.form.get('nuevo_item', '').strip()
    if item:
        lista = cargar_tipos_solicitud()
        if item not in lista:
            lista.append(item)
            guardar_tipos_solicitud(lista)
    return redirect(url_for('gestion', msg='Tipo agregado'))

@app.route('/eliminar_tipo_solicitud', methods=['POST'])
def eliminar_tipo_solicitud():
    if session.get('usuario') != 'admin': return redirect(url_for('gestion'))
    item = request.form.get('tipo', '').strip()
    if item:
        lista = cargar_tipos_solicitud()
        if item in lista:
            lista.remove(item)
            guardar_tipos_solicitud(lista)
    return redirect(url_for('gestion', msg='Tipo eliminado'))

@app.route('/agregar_medio_solicitud', methods=['POST'])
def agregar_medio_solicitud():
    if session.get('usuario') != 'admin': return redirect(url_for('gestion'))
    item = request.form.get('nuevo_item', '').strip()
    if item:
        lista = cargar_medios_solicitud()
        if item not in lista:
            lista.append(item)
            guardar_medios_solicitud(lista)
    return redirect(url_for('gestion', msg='Medio agregado'))

@app.route('/eliminar_medio_solicitud', methods=['POST'])
def eliminar_medio_solicitud():
    if session.get('usuario') != 'admin': return redirect(url_for('gestion'))
    item = request.form.get('medio', '').strip()
    if item:
        lista = cargar_medios_solicitud()
        if item in lista:
            lista.remove(item)
            guardar_medios_solicitud(lista)
    return redirect(url_for('gestion', msg='Medio eliminado'))

# --- ACTIVIDADES PERSONALES ---

@app.route('/agregar_actividad_personal', methods=['POST'])
def agregar_act_personal():
    usuario = session.get('usuario')
    if not usuario: return redirect(url_for('index'))
    
    actividad = request.form.get('nueva_actividad', '').strip()
    if actividad:
        agregar_actividad_personal(usuario, actividad)
        return redirect(url_for('gestion', msg='Actividad personal agregada'))
    return redirect(url_for('gestion', error=1))

@app.route('/eliminar_actividad_personal', methods=['POST'])
def eliminar_act_personal():
    usuario = session.get('usuario')
    if not usuario: return redirect(url_for('index'))
    
    actividad = request.form.get('actividad', '').strip()
    if actividad:
        eliminar_actividad_personal(usuario, actividad)
        return redirect(url_for('gestion', msg='Actividad personal eliminada'))
    return redirect(url_for('gestion', error=1))

# --- CRUD REGISTROS ---

@app.route('/eliminar_registro_accion', methods=['POST'])
def eliminar_registro_route():
    usuario_actual = session.get('usuario')
    if not usuario_actual:
        return redirect(url_for('index'))
        
    id_registro = request.form.get('id_registro')
    if id_registro:
        try:
            if eliminar_registro(int(id_registro), usuario_actual):
                return redirect(url_for('index', deleted=1))
        except ValueError:
            pass
            
    return redirect(url_for('index', error=1))

# =============================================================================
# ESTADÍSTICAS Y EXPORTACIÓN
# =============================================================================

@app.route('/estadisticas')
def estadisticas():
    usuario_actual = session.get('usuario')
    if not usuario_actual: return redirect(url_for('index'))
    
    fecha_inicio = request.args.get('fecha_inicio', '').strip() or None
    fecha_fin = request.args.get('fecha_fin', '').strip() or None

    stats = obtener_estadisticas_exportacion(usuario_actual, fecha_inicio, fecha_fin)
    
    # Calcular promedio
    total = stats.get('total_registros', 0)
    fecha_min = stats.get('fecha_min', 'N/A')
    promedio = "0.0"
    if total > 0 and (fecha_inicio or fecha_min != 'N/A'):
        try:
            base_date = datetime.strptime(fecha_inicio, "%Y-%m-%d") if fecha_inicio else datetime.strptime(fecha_min, "%Y-%m-%d")
            end_date = datetime.strptime(fecha_fin, "%Y-%m-%d") if fecha_fin else datetime.now()
            dias = (end_date - base_date).days + 1
            promedio = f"{total / max(1, dias):.1f}"
        except Exception:
            promedio = "N/A"
    
    # Tabla usuarios
    user_list = stats.get('usuarios', [])
    tabla_stats = ""
    for u in user_list:
        admin_badge = '<span class="badge bg-soft-primary text-primary">Admin</span>' if u['usuario'] == 'admin' else ""
        tabla_stats += f"""
        <tr>
            <td><span class="fw-bold">{u['usuario']}</span> {admin_badge}</td>
            <td class="text-center"><span class="badge bg-light text-dark">{u['total']}</span></td>
            <td class="text-center">{u['cumplimiento']}</td>
            <td class="small text-muted">{u['ultima']}</td>
        </tr>
        """
    if not tabla_stats:
        tabla_stats = "<tr><td colspan='4' class='text-center text-muted'>No hay datos disponibles</td></tr>"
        
    return render_template_string(ESTADISTICAS_TEMPLATE.format(
        usuario_actual=usuario_actual,
        total_registros=total,
        total_tipos_actividad=stats.get('total_tipos_actividad', 0),
        fecha_min=fecha_inicio if fecha_inicio else fecha_min,
        fecha_max=fecha_fin if fecha_fin else stats.get('fecha_max', 'N/A'),
        promedio_diario=promedio,
        data_actividades=json.dumps(stats.get('chart_actividades', {'labels': [], 'data': []})),
        data_cumplimiento=json.dumps(stats.get('chart_cumplimiento', {'labels': [], 'data': []})),
        data_linea=json.dumps(stats.get('chart_linea', {'labels': [], 'data': []})),
        tabla_usuarios_stats=tabla_stats,
        val_fecha_inicio=fecha_inicio or "",
        val_fecha_fin=fecha_fin or ""
    ))

@app.route('/exportar', methods=['GET', 'POST'])
def exportar():
    usuario_actual = session.get('usuario')
    if not usuario_actual: return redirect(url_for('index'))
    
    if request.method == 'GET':
        stats = obtener_estadisticas_exportacion(usuario_actual)
        alertas = ""
        if request.args.get('error'):
            alertas = f'<div class="alert alert-danger">{request.args.get("error")}</div>'
        
        config = obtener_configuracion_usuario(usuario_actual)
        dc = config.get("datos_contrato", {})
        
        # Filtro usuario admin
        filtro_usuario_html = ""
        if usuario_actual == "admin":
            opciones_u = generar_opciones_usuarios()
            filtro_usuario_html = f"""
            <div class="col-md-3">
                <div class="mb-3">
                    <label class="form-label">Filtrar por Usuario</label>
                    <select class="form-select" name="usuario_filtro">
                        <option value="Todos">Todos los usuarios</option>
                        {opciones_u}
                    </select>
                </div>
            </div>
            """
            
        globales = cargar_actividades_globales()
        personales = cargar_actividades(usuario_actual)
        todas = sorted(set(globales + personales))
        opciones = "\\n".join(f'<option value="{a}">{a}</option>' for a in todas)
        
        return render_template_string(EXPORTAR_TEMPLATE.format(
            usuario_actual=usuario_actual,
            opciones_actividades=opciones,
            alertas=alertas,
            fecha_min=stats.get('fecha_min', 'N/A'),
            fecha_max=stats.get('fecha_max', 'N/A'),
            total_registros=stats.get('total_registros', 0),
            total_tipos_actividad=stats.get('total_tipos_actividad', 0),
            ultima_exportacion=stats.get('ultima_exportacion', 'Nunca'),
            filtro_usuario_html=filtro_usuario_html,
            val_contrato_objeto=dc.get('objeto', ''),
            val_contrato_nro=dc.get('nro', ''),
            val_contrato_nombre=dc.get('nombre', ''),
            val_contrato_cedula=dc.get('cedula', ''),
            val_contrato_supervisor=dc.get('supervisor', '')
        ))
        
    if request.method == 'POST':
        import tempfile
        import io
        from export_final_service import generar_informe_final_resumen
        
        fecha_inicio = request.form.get('fecha_inicio', '').strip() or None
        fecha_fin = request.form.get('fecha_fin', '').strip() or None
        actividad = request.form.get('actividad', '').strip() or None
        formato = request.form.get('formato', 'excel').strip()
        tipo_reporte = request.form.get('tipo_reporte', 'detallado').strip()
        usuario_filtro = request.form.get('usuario_filtro', usuario_actual).strip()
        
        contrato_data = {
            'objeto': request.form.get('contrato_objeto', '').strip(),
            'nro': request.form.get('contrato_nro', '').strip(),
            'nombre': request.form.get('contrato_nombre', '').strip(),
            'cedula': request.form.get('contrato_cedula', '').strip(),
            'supervisor': request.form.get('contrato_supervisor', '').strip()
        }
        
        # Guardar config
        config = obtener_configuracion_usuario(usuario_actual)
        config["datos_contrato"] = contrato_data
        guardar_configuracion_usuario(usuario_actual, config)
        
        # Filtros
        if usuario_actual != "admin":
            usuario_filtro = usuario_actual
        elif usuario_filtro == "Todos":
            usuario_filtro = None
            
        df, _ = exportar_registros_filtrados(
            fecha_inicio=fecha_inicio, fecha_fin=fecha_fin,
            usuario=usuario_filtro, actividad=actividad
        )
        
        if df.empty:
            return redirect(url_for('exportar', error='No hay datos para exportar'))
            
        tmp_path = None
        try:
            suffix = '.xlsx' if formato == 'excel' else '.csv'
            fd, tmp_path = tempfile.mkstemp(suffix=suffix)
            os.close(fd)
            
            if formato == 'excel':
                generado = False
                if tipo_reporte == 'final':
                    generado = generar_informe_final_resumen(df, tmp_path, contrato_data=contrato_data)
                else:
                    generado = generar_informe_template(df, tmp_path, contrato_data=contrato_data)
                
                if not generado:
                     return redirect(url_for('exportar', error='No se pudo generar el archivo Excel'))
                
                filename = f"Informe_{tipo_reporte}_{usuario_actual}_{datetime.now().strftime('%Y%m%d')}.xlsx"
                mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            else:
                df.to_csv(tmp_path, index=False, encoding='utf-8')
                filename = f"exportacion_{usuario_actual}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                mimetype = 'text/csv'
                
            # Leer a memoria para enviar y borrar archivo
            with open(tmp_path, 'rb') as f:
                data = io.BytesIO(f.read())
            
            os.remove(tmp_path)
            
            return send_file(
                data,
                as_attachment=True,
                download_name=filename,
                mimetype=mimetype
            )
            
        except Exception as e:
            logger.error(f"Error exportando: {e}")
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
            return redirect(url_for('exportar', error='Error al procesar la exportación'))

# =============================================================================
# INICIALIZACIÓN (Útil para Render/Gunicorn)
# =============================================================================

from database import inicializar_usuarios, inicializar_config, inicializar_excel

def initialize_app():
    with app.app_context():
        try:
            inicializar_usuarios()
            inicializar_config()
            inicializar_excel()
            logger.info("Aplicación inicializada correctamente (Usuarios, Config, Excel)")
        except Exception as e:
            logger.error(f"Error durante la inicialización de la aplicación: {e}")

# Llamar a la inicialización al importar el módulo (para Gunicorn)
initialize_app()

if __name__ == '__main__':
    print("Iniciando servidor Flask local...")
    # Render suele pasar el puerto como variable de entorno
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
