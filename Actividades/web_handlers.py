"""
Controladores de rutas para la aplicación web.
Cada clase maneja una sola ruta o responsabilidad.
"""

import json
import os
import tempfile
from datetime import datetime
from urllib.parse import parse_qs, unquote

from templates import (
    LOGIN_TEMPLATE, MAIN_TEMPLATE, GESTION_TEMPLATE,
    EXPORTAR_TEMPLATE, ESTADISTICAS_TEMPLATE, FORMULARIO_REGISTRO
)
from database import (
    cargar_actividades, cargar_actividades_globales,
    cargar_ubicaciones, guardar_ubicaciones,
    cargar_tipos_solicitud, guardar_tipos_solicitud,
    cargar_medios_solicitud, guardar_medios_solicitud,
    cargar_usuarios, guardar_usuarios,
    guardar_actividades, guardar_registro,
    eliminar_registro, EXCEL_FILE, cargar_registros
)
from activity_service import agregar_actividad_personal, eliminar_actividad_personal
from export_service import (
    exportar_registros_filtrados, obtener_estadisticas_exportacion,
    generar_informe_template
)
from migrate_excel_to_sqlite import import_from_excel
from html_utils import (
    generar_opciones_actividades, generar_opciones_ubicaciones,
    generar_opciones_tipos_solicitud, generar_opciones_medios_solicitud,
    generar_opciones_usuarios, generar_gestion_usuarios,
    generar_gestion_actividades_globales, generar_gestion_actividades_personales,
    generar_gestion_ubicaciones, generar_gestion_tipos_solicitud,
    generar_gestion_medios_solicitud, generar_tabla_registros_recientes
)

# =============================================================================
# CLASE BASE
# =============================================================================

class BaseRoute:
    """Clase base con utilidades compartidas para todos los handlers"""
    
    def __init__(self, request):
        self.request = request
        self.usuario_actual = self._obtener_usuario()

    def _obtener_usuario(self):
        cookies = self.request.headers.get('Cookie', '')
        if 'usuario=' in cookies:
            for cookie in cookies.split(';'):
                if 'usuario=' in cookie.strip():
                    try:
                        return unquote(cookie.strip().split('=')[1])
                    except Exception:
                        return None
        return None

    def get(self, params):
        self.request.send_error(405, "Método no permitido")

    def post(self, params, post_data):
        self.request.send_error(405, "Método no permitido")

    def redirect(self, path):
        self.request.send_response(303)
        self.request.send_header('Location', path)
        self.request.end_headers()

    def render_html(self, html, status=200):
        self.request.send_response(status)
        self.request.send_header('Content-type', 'text/html; charset=utf-8')
        self.request.end_headers()
        self.request.wfile.write(html.encode('utf-8'))

    def send_json(self, data, status=200):
        self.request.send_response(status)
        self.request.send_header('Content-type', 'application/json')
        self.request.end_headers()
        self.request.wfile.write(json.dumps(data).encode('utf-8'))

    def _require_auth(self):
        """Verifica autenticación, redirige si no está logueado"""
        if not self.usuario_actual:
            self.redirect('/')
            return False
        return True

    def _require_admin(self):
        """Verifica que el usuario sea admin"""
        if self.usuario_actual != "admin":
            self.redirect('/gestion?error=No autorizado')
            return False
        return True

# =============================================================================
# HANDLERS DE AUTENTICACIÓN
# =============================================================================

class IndexHandler(BaseRoute):
    """Página principal: muestra login o dashboard según autenticación"""
    def get(self, params):
        if not self.usuario_actual:
            error_login = '<div class="alert alert-danger">Usuario no encontrado</div>' if 'error' in params else ""
            self.render_html(LOGIN_TEMPLATE.format(error_login=error_login))
            return
        
        # Usuario autenticado → mostrar formulario
        alertas = ""
        if 'success' in params:
            alertas = '<div class="alert alert-success alert-dismissible fade show">✅ Registro guardado<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
        elif 'error' in params:
            alertas = f'<div class="alert alert-danger alert-dismissible fade show">❌ {params.get("error", ["Error"])[0]}<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
        elif 'deleted' in params:
            alertas = '<div class="alert alert-info alert-dismissible fade show">🗑️ Registro eliminado<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
        
        # Cargar registros para la tabla
        df = cargar_registros(None if self.usuario_actual == 'admin' else self.usuario_actual)
        tabla_html = generar_tabla_registros_recientes(df, self.usuario_actual)

        # Generar sección de registro solo si no es admin
        seccion_registro = ""
        if self.usuario_actual != 'admin':
            seccion_registro = FORMULARIO_REGISTRO.format(
                opciones_actividades=generar_opciones_actividades(self.usuario_actual),
                opciones_ubicaciones=generar_opciones_ubicaciones(),
                opciones_tipos=generar_opciones_tipos_solicitud(),
                opciones_medios=generar_opciones_medios_solicitud(),
                fecha_hoy=datetime.now().strftime('%Y-%m-%d')
            )

        html = MAIN_TEMPLATE.format(
            usuario_actual=self.usuario_actual,
            seccion_registro=seccion_registro,
            alertas=alertas,
            tabla_registros=tabla_html
        )
        self.render_html(html)


class LoginHandler(BaseRoute):
    """Procesa el login: establece cookie de sesión"""
    def post(self, params, post_data):
        data = parse_qs(post_data)
        usuario = data.get('usuario', [''])[0].strip()
        clave = data.get('clave', [''])[0].strip()
        
        if usuario:
            # Verificar que el usuario existe
            usuarios_data = cargar_usuarios()
            usuarios = usuarios_data.get("usuarios", [])
            encontrado = next((u for u in usuarios if u.lower() == usuario.lower()), None)
            
            if encontrado:
                if encontrado.lower() == 'admin':
                    import os
                    admin_secret = os.environ.get('ADMIN_SECRET')
                    if admin_secret and clave != admin_secret:
                        self.redirect('/?error=1')
                        return
                self.request.send_response(303)
                self.request.send_header('Location', '/')
                self.request.send_header('Set-Cookie', f'usuario={encontrado}; Path=/; Max-Age=3600')
                self.request.end_headers()
                return
        
        self.redirect('/?error=1')


class LogoutHandler(BaseRoute):
    """Cierra sesión eliminando la cookie"""
    def get(self, params):
        self.request.send_response(303)
        self.request.send_header('Location', '/')
        self.request.send_header('Set-Cookie', 'usuario=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT')
        self.request.end_headers()

    def post(self, params, post_data):
        self.get(params)

# =============================================================================
# HANDLERS DE PÁGINAS
# =============================================================================

class GestionHandler(BaseRoute):
    """Página de gestión de actividades y usuarios"""
    def get(self, params):
        if not self._require_auth():
            return
        
        alertas = ""
        if 'msg' in params or 'success' in params:
            msg = params.get('msg', ['Operación exitosa'])[0] if 'msg' in params else 'Operación exitosa'
            alertas = f'<div class="alert alert-success alert-dismissible fade show">✅ {msg}<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
        elif 'error' in params:
            alertas = '<div class="alert alert-danger alert-dismissible fade show">❌ Error en la operación<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
        
        gestion_usuarios = generar_gestion_usuarios(self.usuario_actual) if self.usuario_actual == "admin" else ""
        gestion_ubicaciones = generar_gestion_ubicaciones() if self.usuario_actual == "admin" else ""
        gestion_tipos = generar_gestion_tipos_solicitud() if self.usuario_actual == "admin" else ""
        gestion_medios = generar_gestion_medios_solicitud() if self.usuario_actual == "admin" else ""
        gestion_personal = generar_gestion_actividades_personales(self.usuario_actual) if self.usuario_actual != "admin" else ""
        
        # Cargar datos de contrato para el formulario
        from database import obtener_configuracion_usuario
        config = obtener_configuracion_usuario(self.usuario_actual)
        dc = config.get("datos_contrato", {})
        
        html = GESTION_TEMPLATE.format(
            usuario_actual=self.usuario_actual,
            gestion_actividades=f"{gestion_ubicaciones}{gestion_tipos}{gestion_medios}",
            gestion_usuarios=gestion_usuarios,
            gestion_personal=gestion_personal,
            alertas=alertas,
            datos_nro=dc.get('nro', ''),
            datos_objeto=dc.get('objeto', ''),
            datos_nombre=dc.get('nombre', ''),
            datos_cedula=dc.get('cedula', ''),
            datos_supervisor=dc.get('supervisor', '')
        )
        self.render_html(html)


class EstadisticasHandler(BaseRoute):
    """Página de estadísticas y gráficos"""
    def get(self, params):
        if not self._require_auth():
            return
        
        fecha_inicio = params.get('fecha_inicio', [''])[0].strip() or None
        fecha_fin = params.get('fecha_fin', [''])[0].strip() or None

        stats = obtener_estadisticas_exportacion(self.usuario_actual, fecha_inicio, fecha_fin)
        
        # Calcular promedio diario
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
        
        # Generar tabla de usuarios stats
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

        html = ESTADISTICAS_TEMPLATE.format(
            usuario_actual=self.usuario_actual,
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
        )
        self.render_html(html)


class ExportarHandler(BaseRoute):
    """Página y procesamiento de exportación de datos"""
    def get(self, params):
        if not self._require_auth():
            return
        
        stats = obtener_estadisticas_exportacion(self.usuario_actual)
        alertas = ""
        if 'error' in params:
            msg = params['error'][0] if isinstance(params.get('error'), list) else 'Error'
            alertas = f'<div class="alert alert-danger">{msg}</div>'
        
        # Cargar datos de contrato persistidos
        from database import obtener_configuracion_usuario
        config = obtener_configuracion_usuario(self.usuario_actual)
        dc = config.get("datos_contrato", {})
        
        # Fallback: si el usuario no tiene datos de contrato, usar los del admin
        if not any(dc.get(k) for k in ['objeto', 'nro', 'nombre', 'cedula', 'supervisor']):
            try:
                admin_config = obtener_configuracion_usuario('admin')
                admin_dc = admin_config.get("datos_contrato", {}) if isinstance(admin_config, dict) else {}
                if any(admin_dc.get(k) for k in ['objeto', 'nro', 'nombre', 'cedula', 'supervisor']):
                    dc = admin_dc
            except Exception:
                pass

        # Filtro de usuario solo para admin
        filtro_usuario_html = ""
        if self.usuario_actual == "admin":
            opciones_u = generar_opciones_usuarios()
            filtro_usuario_html = f"""
            <div class="col-md-3">
                <div class="mb-3">
                    <label class="form-label">Filtrar por Usuario</label>
                    <select class="form-select" name="usuario_filtro">
                        <option value="Todos" selected>Todos los usuarios</option>
                        {opciones_u}
                    </select>
                </div>
            </div>
            """
            importar_html = """
            <div class="card mb-4">
              <div class="card-header">
                <h5><i class="fas fa-file-import"></i> Importar desde Excel (no destructivo)</h5>
              </div>
              <div class="card-body">
                <form method="POST" action="/importar_excel">
                  <div class="row">
                    <div class="col-md-8">
                      <label class="form-label">Ruta del archivo .xlsx</label>
                      <input type="text" class="form-control" name="excel_path" placeholder="C:\\\\ruta\\\\archivo.xlsx" required>
                      <div class="form-text">Hace respaldo automático y evita duplicados exactos.</div>
                    </div>
                    <div class="col-md-4 d-flex align-items-end">
                      <button type="submit" class="btn btn-success">
                        <i class="fas fa-upload"></i> Importar
                      </button>
                    </div>
                  </div>
                </form>
              </div>
            </div>
            """
        else:
            importar_html = ""

        # Opciones de actividades para el filtro
        personales = cargar_actividades(self.usuario_actual)
        todas = sorted(set(personales))
        opciones = "\n".join(f'<option value="{a}">{a}</option>' for a in todas)
        
        html = EXPORTAR_TEMPLATE.format(
            usuario_actual=self.usuario_actual,
            opciones_actividades=opciones,
            alertas=alertas,
            fecha_min=stats.get('fecha_min', 'N/A'),
            fecha_max=stats.get('fecha_max', 'N/A'),
            total_registros=stats.get('total_registros', 0),
            total_tipos_actividad=stats.get('total_tipos_actividad', 0),
            ultima_exportacion=stats.get('ultima_exportacion', 'Nunca'),
            filtro_usuario_html=filtro_usuario_html,
            importar_html=importar_html,
            val_contrato_objeto=dc.get('objeto', ''),
            val_contrato_nro=dc.get('nro', ''),
            val_contrato_nombre=dc.get('nombre', ''),
            val_contrato_cedula=dc.get('cedula', ''),
            val_contrato_supervisor=dc.get('supervisor', '')
        )
        self.render_html(html)

    def post(self, params, post_data):
        if not self._require_auth():
            return
        
        data = parse_qs(post_data)
        fecha_inicio = data.get('fecha_inicio', [''])[0].strip() or None
        fecha_fin = data.get('fecha_fin', [''])[0].strip() or None
        actividad = data.get('actividad', [''])[0].strip() or None
        formato = data.get('formato', ['excel'])[0].strip()
        tipo_reporte = data.get('tipo_reporte', ['detallado'])[0].strip()
        from config import logger
        logger.info(f"POST /exportar - tipo_reporte recibido: {tipo_reporte}")
        usuario_filtro = data.get('usuario_filtro', [self.usuario_actual])[0].strip()
        
        # Datos adicionales del contrato
        contrato_data = {
            'objeto': data.get('contrato_objeto', [''])[0].strip(),
            'nro': data.get('contrato_nro', [''])[0].strip(),
            'nombre': data.get('contrato_nombre', [''])[0].strip(),
            'cedula': data.get('contrato_cedula', [''])[0].strip(),
            'supervisor': data.get('contrato_supervisor', [''])[0].strip()
        }

        # Fallback
        if not any(contrato_data.values()):
            try:
                from database import obtener_configuracion_usuario as _ocu
                admin_cfg = _ocu('admin')
                admin_dc = admin_cfg.get('datos_contrato', {}) if isinstance(admin_cfg, dict) else {}
                if any(admin_dc.values()):
                    contrato_data = admin_dc
            except Exception:
                pass

        # Guardar estos datos
        from database import obtener_configuracion_usuario, guardar_configuracion_usuario
        config = obtener_configuracion_usuario(self.usuario_actual)
        config["datos_contrato"] = contrato_data
        guardar_configuracion_usuario(self.usuario_actual, config)
        
        # Admin puede elegir "Todos"
        if self.usuario_actual != "admin":
            usuario_filtro = self.usuario_actual
        elif usuario_filtro == "Todos":
            usuario_filtro = None

        df, _ = exportar_registros_filtrados(
            fecha_inicio=fecha_inicio, fecha_fin=fecha_fin,
            usuario=usuario_filtro, actividad=actividad
        )
        
        if df.empty:
            self.redirect('/exportar?error=No hay datos para exportar')
            return
        
        tmp_path = None
        try:
            suffix = '.xlsx' if formato == 'excel' else '.csv'
            fd, tmp_path = tempfile.mkstemp(suffix=suffix)
            os.close(fd)
            
            if formato == 'excel':
                generado = False
                if tipo_reporte == 'final':
                    from export_final_service import generar_informe_final_resumen
                    generado = generar_informe_final_resumen(df, tmp_path, contrato_data=contrato_data, usuario=usuario_filtro)
                else:
                    generado = generar_informe_template(df, tmp_path, contrato_data=contrato_data)
                
                if not generado:
                    self.redirect('/exportar?error=No se pudo generar el archivo Excel')
                    return
                content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                filename = f"Informe_{tipo_reporte}_{self.usuario_actual}_{datetime.now().strftime('%Y%m%d')}.xlsx"
            else:
                df.to_csv(tmp_path, index=False, encoding='utf-8-sig')
                content_type = 'text/csv; charset=utf-8-sig'
                filename = f"exportacion_{self.usuario_actual}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            with open(tmp_path, 'rb') as f:
                file_data = f.read()
        except Exception as e:
            from config import logger
            logger.exception(f"Error crítico en ExportarHandler.post: {e}")
            self.redirect('/exportar?error=Error al procesar la exportación')
            return
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception as e:
                    from config import logger
                    logger.error(f"No se pudo eliminar el archivo temporal {tmp_path}: {e}")
        
        self.request.send_response(200)
        self.request.send_header('Content-Type', content_type)
        self.request.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.request.send_header('Content-Length', str(len(file_data)))
        self.request.end_headers()
        self.request.wfile.write(file_data)

class ImportarExcelHandler(BaseRoute):
    """Importa registros desde un archivo Excel, solo admin"""
    def get(self, params):
        self.redirect('/exportar')
    def post(self, params, post_data):
        if not self._require_admin():
            return
        data = parse_qs(post_data)
        excel_path = data.get('excel_path', [''])[0].strip()
        if not excel_path:
            self.redirect('/exportar?error=Ruta de Excel vacía')
            return
        try:
            count = import_from_excel(excel_path)
            self.redirect(f'/exportar?success=Importados {count} registros desde Excel')
        except FileNotFoundError:
            self.redirect('/exportar?error=No se encontró el archivo Excel')
        except Exception as e:
            from config import logger
            logger.exception(f"Error en importación desde Excel: {e}")
            self.redirect('/exportar?error=Error al importar. Revisa el log.')

# =============================================================================
# HANDLERS DE ACCIONES (POST)
# =============================================================================

class GuardarRegistroHandler(BaseRoute):
    """Guarda un nuevo registro de actividad"""
    def post(self, params, post_data):
        from config import logger
        if not self._require_auth():
            return
        
        data = parse_qs(post_data)
        ahora = datetime.now()
        
        logger.info(f"Recibida solicitud de registro para usuario: {self.usuario_actual}")
        
        fecha_ingresada = data.get('fecha_atencion', [ahora.strftime('%Y-%m-%d')])[0].strip()
        if not fecha_ingresada:
            fecha_ingresada = ahora.strftime('%Y-%m-%d')
            
        fecha_con_hora = f"{fecha_ingresada} {ahora.strftime('%H:%M:%S')}"
        
        registro = {
            'USUARIO': self.usuario_actual,
            'FECHA': fecha_con_hora,
            'TIPO DE ACTIVIDAD': data.get('actividad', [''])[0],
            'DEPENDENCIA': data.get('ubicacion', [''])[0],
            'SOLICITANTE': data.get('solicitante', [''])[0],
            'TIPO DE SOLICITUD': data.get('tipo_solicitud', [''])[0],
            'MEDIO DE SOLICITUD': data.get('medio_solicitud', [''])[0],
            'CUMPLIDO': data.get('cumplido', ['Sí'])[0],
            'FECHA ATENCIÓN': fecha_ingresada,
            'DESCRIPCIÓN': data.get('descripcion', data.get('observaciones', ['']))[0],
            'OBSERVACIONES': data.get('observaciones', [''])[0]
        }
        
        res = guardar_registro(registro)
        if res:
            logger.info(f"Registro guardado exitosamente con ID: {res}")
            self.redirect('/?success=1')
        else:
            logger.error(f"Fallo al guardar registro para usuario: {self.usuario_actual}")
            self.redirect('/?error=1')


class EliminarRegistroAccionHandler(BaseRoute):
    """Elimina un registro con verificación de propiedad"""
    def post(self, params, post_data):
        if not self._require_auth():
            return
        
        data = parse_qs(post_data)
        id_reg = data.get('id_registro', [''])[0].strip()
        
        if id_reg:
            try:
                if eliminar_registro(int(id_reg), self.usuario_actual):
                    self.redirect('/?deleted=1')
                    return
            except Exception:
                pass
        
        self.redirect('/?error=Error al eliminar')


class UserAdminHandler(BaseRoute):
    """Agrega o elimina usuarios (solo admin)"""
    def post(self, params, post_data):
        if not self._require_admin():
            return
        
        data = parse_qs(post_data)
        path = self.request.path.split('?')[0]
        
        if path == '/agregar_usuario':
            nuevo = data.get('nuevo_usuario', [''])[0].strip()
            if nuevo:
                u_data = cargar_usuarios()
                usuarios = u_data.get("usuarios", [])
                if nuevo not in usuarios:
                    usuarios.append(nuevo)
                    u_data["usuarios"] = usuarios
                    if "actividades" not in u_data:
                        u_data["actividades"] = {}
                    u_data["actividades"][nuevo] = []
                    guardar_usuarios(u_data)
                    self.redirect('/gestion?msg=Usuario agregado')
                    return
        
        elif path == '/eliminar_usuario':
            eliminar = data.get('usuario', [''])[0].strip()
            if eliminar and eliminar != "admin":
                u_data = cargar_usuarios()
                usuarios = u_data.get("usuarios", [])
                if eliminar in usuarios:
                    usuarios.remove(eliminar)
                    u_data["usuarios"] = usuarios
                    if "actividades" in u_data and eliminar in u_data["actividades"]:
                        del u_data["actividades"][eliminar]
                    guardar_usuarios(u_data)
                    self.redirect('/gestion?msg=Usuario eliminado')
                    return
        
        self.redirect('/gestion')


class ConfigAdminHandler(BaseRoute):
    """Gestiona actividades globales, personales, ubicaciones, tipos y medios"""
    def post(self, params, post_data):
        if not self._require_auth():
            return
        
        data = parse_qs(post_data)
        path = self.request.path.split('?')[0]
        nuevo_item = data.get('nuevo_item', [''])[0].strip()
        
        # --- ACTIVIDADES GLOBALES ---
        if path == '/agregar_actividad_global':
            if not self._require_admin(): return
            if nuevo_item:
                act = cargar_actividades_globales()
                if nuevo_item not in act:
                    act.append(nuevo_item)
                    guardar_actividades(act)
                    self.redirect('/gestion?msg=Actividad global agregada')
                    return
                else:
                    self.redirect('/gestion?error=La actividad ya existe')
                    return
        
        elif path == '/eliminar_actividad_global':
            if not self._require_admin(): return
            actividad = data.get('actividad', [''])[0].strip()
            if actividad:
                act = cargar_actividades_globales()
                if actividad in act:
                    act.remove(actividad)
                    guardar_actividades(act)
                    self.redirect('/gestion?msg=Actividad global eliminada')
                    return

        # --- UBICACIONES ---
        elif path == '/agregar_ubicacion':
            if not self._require_admin(): return
            if nuevo_item:
                items = cargar_ubicaciones()
                if nuevo_item not in items:
                    items.append(nuevo_item)
                    guardar_ubicaciones(items)
                    self.redirect('/gestion?msg=Ubicación agregada')
                    return
        
        elif path == '/eliminar_ubicacion':
            if not self._require_admin(): return
            item = data.get('ubicacion', [''])[0].strip()
            if item:
                items = cargar_ubicaciones()
                if item in items:
                    items.remove(item)
                    guardar_ubicaciones(items)
                    self.redirect('/gestion?msg=Ubicación eliminada')
                    return

        # --- TIPOS DE SOLICITUD ---
        elif path == '/agregar_tipo_solicitud':
            if not self._require_admin(): return
            if nuevo_item:
                items = cargar_tipos_solicitud()
                if nuevo_item not in items:
                    items.append(nuevo_item)
                    guardar_tipos_solicitud(items)
                    self.redirect('/gestion?msg=Tipo de solicitud agregado')
                    return
        
        elif path == '/eliminar_tipo_solicitud':
            if not self._require_admin(): return
            item = data.get('tipo', [''])[0].strip()
            if item:
                items = cargar_tipos_solicitud()
                if item in items:
                    items.remove(item)
                    guardar_tipos_solicitud(items)
                    self.redirect('/gestion?msg=Tipo de solicitud eliminado')
                    return

        # --- MEDIOS DE SOLICITUD ---
        elif path == '/agregar_medio_solicitud':
            if not self._require_admin(): return
            if nuevo_item:
                items = cargar_medios_solicitud()
                if nuevo_item not in items:
                    items.append(nuevo_item)
                    guardar_medios_solicitud(items)
                    self.redirect('/gestion?msg=Medio de solicitud agregado')
                    return
        
        elif path == '/eliminar_medio_solicitud':
            if not self._require_admin(): return
            item = data.get('medio', [''])[0].strip()
            if item:
                items = cargar_medios_solicitud()
                if item in items:
                    items.remove(item)
                    guardar_medios_solicitud(items)
                    self.redirect('/gestion?msg=Medio de solicitud eliminado')
                    return

        # --- ACTIVIDADES PERSONALES ---
        elif path == '/agregar_actividad_personal':
            nueva = data.get('nueva_actividad', nuevo_item if nuevo_item else [''])[0].strip()
            if nueva:
                if agregar_actividad_personal(self.usuario_actual, nueva):
                    self.redirect('/gestion?msg=Actividad personal agregada')
                else:
                    self.redirect('/gestion?error=La actividad ya existe o hubo un error')
                return
        
        elif path == '/eliminar_actividad_personal':
            actividad = data.get('actividad', [''])[0].strip()
            if actividad:
                eliminar_actividad_personal(self.usuario_actual, actividad)
                self.redirect('/gestion?msg=Actividad personal eliminada')
                return
        
        self.redirect('/gestion')


class GuardarDatosContratoHandler(BaseRoute):
    """Guarda los datos del contrato del usuario"""
    def post(self, params, post_data):
        if not self._require_auth():
            return
            
        data = parse_qs(post_data)
        contrato_data = {
            'objeto': data.get('objeto', [''])[0].strip(),
            'nro': data.get('nro', [''])[0].strip(),
            'nombre': data.get('nombre', [''])[0].strip(),
            'cedula': data.get('cedula', [''])[0].strip(),
            'supervisor': data.get('supervisor', [''])[0].strip()
        }
        
        from database import obtener_configuracion_usuario, guardar_configuracion_usuario
        config = obtener_configuracion_usuario(self.usuario_actual)
        config["datos_contrato"] = contrato_data
        
        if guardar_configuracion_usuario(self.usuario_actual, config):
            self.redirect('/gestion?msg=Datos del contrato guardados')
        else:
            self.redirect('/gestion?error=1')


class EditarRegistroHandler(BaseRoute):
    """Muestra el formulario para editar un registro existente"""
    def get(self, params):
        if not self._require_auth():
            return
            
        id_reg = params.get('id_registro', [''])[0].strip()
        if not id_reg:
            self.redirect('/?error=ID de registro no proporcionado')
            return
            
        try:
            # Cargar todos los registros del usuario (o todos si es admin)
            df = cargar_registros(None if self.usuario_actual == 'admin' else self.usuario_actual)
            # Buscar el registro por ID
            registro = df[df['ID'].astype(str) == id_reg]
            
            if registro.empty:
                self.redirect('/?error=Registro no encontrado')
                return
                
            reg_data = registro.iloc[0]
            
            # Preparar datos para el template
            from templates import EDIT_REGISTRO_TEMPLATE
            from html_utils import (
                generar_opciones_con_seleccion, cargar_actividades, cargar_ubicaciones,
                cargar_tipos_solicitud, cargar_medios_solicitud
            )
            
            html = EDIT_REGISTRO_TEMPLATE.format(
                usuario_actual=self.usuario_actual,
                id_reg=id_reg,
                opciones_actividades=generar_opciones_con_seleccion(cargar_actividades(self.usuario_actual), reg_data.get('TIPO DE ACTIVIDAD', '')),
                opciones_ubicaciones=generar_opciones_con_seleccion(cargar_ubicaciones(), reg_data.get('DEPENDENCIA', '')),
                opciones_tipos=generar_opciones_con_seleccion(cargar_tipos_solicitud(), reg_data.get('TIPO DE SOLICITUD', '')),
                opciones_medios=generar_opciones_con_seleccion(cargar_medios_solicitud(), reg_data.get('MEDIO DE SOLICITUD', '')),
                val_solicitante=reg_data.get('SOLICITANTE', ''),
                sel_cumplido_si='selected' if reg_data.get('CUMPLIDO', '') == 'Sí' else '',
                sel_cumplido_no='selected' if reg_data.get('CUMPLIDO', '') == 'No' else '',
                val_fecha_atencion=reg_data.get('FECHA ATENCIÓN', ''),
                val_observaciones=reg_data.get('OBSERVACIONES', '')
            )
            self.render_html(html)
        except Exception as e:
            from config import logger
            logger.exception(f"Error en EditarRegistroHandler: {e}")
            self.redirect(f'/?error=Error al cargar edición: {str(e)}')


class ActualizarRegistroAccionHandler(BaseRoute):
    """Procesa la actualización de un registro"""
    def post(self, params, post_data):
        if not self._require_auth():
            return
            
        data = parse_qs(post_data)
        id_reg = data.get('id_registro', [''])[0].strip()
        
        if not id_reg:
            self.redirect('/?error=Falta ID de registro')
            return
            
        registro_update = {
            'TIPO DE ACTIVIDAD': data.get('actividad', [''])[0],
            'DEPENDENCIA': data.get('ubicacion', [''])[0],
            'SOLICITANTE': data.get('solicitante', [''])[0],
            'TIPO DE SOLICITUD': data.get('tipo_solicitud', [''])[0],
            'MEDIO DE SOLICITUD': data.get('medio_solicitud', [''])[0],
            'CUMPLIDO': data.get('cumplido', ['Sí'])[0],
            'FECHA ATENCIÓN': data.get('fecha_atencion', [''])[0],
            'OBSERVACIONES': data.get('observaciones', [''])[0],
            'DESCRIPCIÓN': data.get('observaciones', [''])[0]
        }
        
        from database import actualizar_registro
        if actualizar_registro(int(id_reg), registro_update, self.usuario_actual):
            self.redirect('/?success=Registro actualizado correctamente')
        else:
            self.redirect('/?error=No se pudo actualizar el registro')

# =============================================================================
# HANDLERS DE API Y ARCHIVOS ESTÁTICOS
# =============================================================================

class APIHandler(BaseRoute):
    """Endpoints API que devuelven JSON"""
    def get(self, params):
        path = self.request.path.split('?')[0]
        
        if path == '/api/actividades':
            self.send_json(cargar_actividades(self.usuario_actual))
        elif path == '/api/estadisticas_exportacion':
            self.send_json(obtener_estadisticas_exportacion(self.usuario_actual))
        else:
            self.request.send_error(404)


class StaticHandler(BaseRoute):
    """Descarga de archivos estáticos"""
    def get(self, params):
        if not os.path.exists(EXCEL_FILE):
            self.request.send_error(404, "Archivo no encontrado")
            return
        
        with open(EXCEL_FILE, 'rb') as f:
            content = f.read()
        
        self.request.send_response(200)
        self.request.send_header('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.request.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(EXCEL_FILE)}"')
        self.request.send_header('Content-Length', str(len(content)))
        self.request.end_headers()
        self.request.wfile.write(content)

# =============================================================================
# MAPA DE RUTAS
# =============================================================================

ROUTE_MAP = {
    '/': IndexHandler,
    '/login': LoginHandler,
    '/logout': LogoutHandler,
    '/gestion': GestionHandler,
    '/estadisticas': EstadisticasHandler,
    '/exportar': ExportarHandler,
    '/guardar': GuardarRegistroHandler,
    '/agregar_registro': GuardarRegistroHandler,
    '/eliminar_registro_accion': EliminarRegistroAccionHandler,
    '/editar_registro': EditarRegistroHandler,
    '/actualizar_registro_accion': ActualizarRegistroAccionHandler,
    '/agregar_usuario': UserAdminHandler,
    '/eliminar_usuario': UserAdminHandler,
    '/agregar_actividad_global': ConfigAdminHandler,
    '/eliminar_actividad_global': ConfigAdminHandler,
    '/agregar_actividad_personal': ConfigAdminHandler,
    '/eliminar_actividad_personal': ConfigAdminHandler,
    '/agregar_ubicacion': ConfigAdminHandler,
    '/eliminar_ubicacion': ConfigAdminHandler,
    '/agregar_tipo_solicitud': ConfigAdminHandler,
    '/eliminar_tipo_solicitud': ConfigAdminHandler,
    '/agregar_medio_solicitud': ConfigAdminHandler,
    '/eliminar_medio_solicitud': ConfigAdminHandler,
    '/guardar_datos_contrato': GuardarDatosContratoHandler,
    '/importar_excel': ImportarExcelHandler,
    '/api/actividades': APIHandler,
    '/api/estadisticas_exportacion': APIHandler,
    '/descargar_excel': StaticHandler,
}
