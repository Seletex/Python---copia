"""
Módulo de handlers HTTP para la aplicación web
"""

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from datetime import datetime
import functools
import json
import os
import tempfile

from config import (
    LOGIN_TEMPLATE, MAIN_TEMPLATE, GESTION_TEMPLATE,
    EXPORTAR_TEMPLATE, ESTADISTICAS_TEMPLATE
)
from database import (
    inicializar_usuarios, inicializar_config, inicializar_excel,
    cargar_usuarios, guardar_usuarios, cargar_registros, guardar_registro,
    agregar_actividad_personal, eliminar_actividad_personal,
    guardar_actividades, guardar_ubicaciones, guardar_tipos_solicitud, guardar_medios_solicitud,
    cargar_actividades, cargar_actividades_globales
)
from html_utils import (
    generar_opciones_actividades, generar_opciones_ubicaciones,
    generar_opciones_tipos_solicitud, generar_opciones_medios_solicitud,
    generar_opciones_usuarios, generar_gestion_actividades_globales,
    generar_gestion_usuarios, generar_gestion_actividades_personales
)
from utils import medir_tiempo

class RequestHandler(BaseHTTPRequestHandler):
    """Handler HTTP para manejar todas las solicitudes de la aplicación"""
    
    # Cache de sesiones
    sesiones = {}
    
    def do_GET(self):
        """Maneja solicitudes GET"""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            # Verificar autenticación
            usuario_actual = self.verificar_autenticacion()
            
            if path == '/':
                self.serve_login()
            elif path == '/main':
                if usuario_actual:
                    self.serve_main(usuario_actual)
                else:
                    self.redirect('/')
            elif path == '/logout':
                self.cerrar_sesion()
                self.redirect('/')
            elif path == '/gestion':
                if usuario_actual:
                    self.serve_gestion(usuario_actual)
                else:
                    self.redirect('/')
            elif path == '/estadisticas':
                if usuario_actual:
                    self.serve_estadisticas(usuario_actual)
                else:
                    self.redirect('/')
            elif path == '/exportar':
                if usuario_actual:
                    self.serve_exportar(usuario_actual)
                else:
                    self.redirect('/')
            else:
                self.send_error(404, "Página no encontrada")
                
        except Exception as e:
            print(f"Error en GET {self.path}: {e}")
            self.send_error(500, f"Error interno: {e}")
    
    def do_POST(self):
        """Maneja solicitudes POST"""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            # Leer datos del formulario
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            form_data = parse_qs(post_data)
            
            usuario_actual = self.verificar_autenticacion()
            
            if path == '/login':
                self.procesar_login(form_data)
            elif path == '/agregar_registro':
                if usuario_actual:
                    self.procesar_agregar_registro(form_data, usuario_actual)
                else:
                    self.redirect('/')
            elif path == '/agregar_actividad_global':
                if usuario_actual == 'admin':
                    self.procesar_agregar_actividad_global(form_data)
                else:
                    self.redirect('/')
            elif path == '/eliminar_actividad_global':
                if usuario_actual == 'admin':
                    self.procesar_eliminar_actividad_global(form_data)
                else:
                    self.redirect('/')
            elif path == '/agregar_actividad_personal':
                if usuario_actual:
                    self.procesar_agregar_actividad_personal(form_data, usuario_actual)
                else:
                    self.redirect('/')
            elif path == '/eliminar_actividad_personal':
                if usuario_actual:
                    self.procesar_eliminar_actividad_personal(form_data, usuario_actual)
                else:
                    self.redirect('/')
            elif path == '/agregar_usuario':
                if usuario_actual == 'admin':
                    self.procesar_agregar_usuario(form_data)
                else:
                    self.redirect('/')
            elif path == '/eliminar_usuario':
                if usuario_actual == 'admin':
                    self.procesar_eliminar_usuario(form_data)
                else:
                    self.redirect('/')
            elif path == '/procesar_exportacion':
                if usuario_actual:
                    self.procesar_exportacion(form_data, usuario_actual)
                else:
                    self.redirect('/')
            else:
                self.send_error(404, "Acción no encontrada")
                
        except Exception as e:
            with open('debug_post.txt', 'a') as f:
                f.write(f"ERROR en do_POST: {str(e)}\n")
            print(f"Error en POST {self.path}: {e}")
            self.send_error(500, f"Error interno: {e}")
    
    # =========================================================================
    # MÉTODOS AUXILIARES
    # =========================================================================
    
    def verificar_autenticacion(self):
        """Verifica si el usuario está autenticado"""
        cookies = self.parse_cookies()
        session_id = cookies.get('session_id')
        
        if session_id and session_id in self.sesiones:
            return self.sesiones[session_id]
        return None
    
    def parse_cookies(self):
        """Parsea las cookies del header"""
        cookies = {}
        if 'Cookie' in self.headers:
            cookie_header = self.headers['Cookie']
            for cookie in cookie_header.split(';'):
                if '=' in cookie:
                    key, value = cookie.strip().split('=', 1)
                    cookies[key] = value
        return cookies
    
    def set_cookie(self, name, value, max_age=3600):
        """Encola una cookie para ser enviada"""
        if not hasattr(self, 'pending_cookies'):
            self.pending_cookies = []
        self.pending_cookies.append(f'{name}={value}; Max-Age={max_age}; Path=/')

    def enviar_cookies_pendientes(self):
        """Envía las cookies pendientes (debe llamarse después de send_response)"""
        if hasattr(self, 'pending_cookies'):
            for cookie in self.pending_cookies:
                self.send_header('Set-Cookie', cookie)
            self.pending_cookies = []  # Limpiar después de enviar
    
    def redirect(self, location):
        """Redirecciona a otra URL"""
        self.send_response(302)
        self.send_header('Location', location)
        self.enviar_cookies_pendientes()
        self.end_headers()
    
    def servir_html(self, html, status=200):
        """Sirve contenido HTML"""
        self.send_response(status)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.enviar_cookies_pendientes()
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def servir_json(self, data, status=200):
        """Sirve contenido JSON"""
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.enviar_cookies_pendientes()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def iniciar_sesion(self, usuario):
        """Inicia sesión para un usuario"""
        session_id = str(hash(f"{usuario}{datetime.now().timestamp()}"))
        self.sesiones[session_id] = usuario
        self.set_cookie('session_id', session_id)
        return session_id
    
    def cerrar_sesion(self):
        """Cierra la sesión actual"""
        cookies = self.parse_cookies()
        session_id = cookies.get('session_id')
        if session_id and session_id in self.sesiones:
            del self.sesiones[session_id]
        self.set_cookie('session_id', '', max_age=0)
    
    # =========================================================================
    # MÉTODOS PARA PÁGINAS PRINCIPALES
    # =========================================================================
    
    @medir_tiempo
    def serve_login(self):
        """Sirve la página de login"""
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        error_login = ""
        
        if 'error' in query_params:
            error_login = """
            <div class="alert alert-danger">
                ❌ Usuario no válido
            </div>
            """
            
        html = LOGIN_TEMPLATE.format(error_login=error_login)
        self.servir_html(html)
    
    @medir_tiempo
    def serve_main(self, usuario_actual):
        """Sirve la página principal"""
        # Generar opciones para los dropdowns
        opciones_actividades = generar_opciones_actividades(usuario_actual)
        opciones_ubicaciones = generar_opciones_ubicaciones()
        opciones_tipos = generar_opciones_tipos_solicitud()
        opciones_medios = generar_opciones_medios_solicitud()
        
        # Generar alertas
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        alertas = ""
        
        if 'success' in query_params:
            alertas = """
            <div class="alert alert-success alert-dismissible fade show">
                ✅ Registro agregado correctamente
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
            """
        elif 'error' in query_params:
            alertas = """
            <div class="alert alert-danger alert-dismissible fade show">
                ❌ Error al agregar registro
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
            """
        
        html = MAIN_TEMPLATE.format(
            usuario_actual=usuario_actual,
            opciones_actividades=opciones_actividades,
            opciones_ubicaciones=opciones_ubicaciones,
            opciones_tipos=opciones_tipos,
            opciones_medios=opciones_medios,
            alertas=alertas,
            fecha_hoy=datetime.now().strftime('%Y-%m-%d')
        )
        self.servir_html(html)
    
    @medir_tiempo
    def serve_gestion(self, usuario_actual):
        """Sirve la página de gestión"""
        # Generar contenido de gestión según el usuario
        if usuario_actual == 'admin':
            gestion_actividades = generar_gestion_actividades_globales()
            gestion_usuarios = generar_gestion_usuarios(usuario_actual)
            gestion_personal = ""
        else:
            gestion_actividades = ""
            gestion_usuarios = ""
            gestion_personal = generar_gestion_actividades_personales(usuario_actual)
        
        # Generar alertas
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        alertas = ""
        
        if 'success' in query_params:
            alertas = """
            <div class="alert alert-success alert-dismissible fade show">
                ✅ Operación realizada correctamente
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
            """
        elif 'error' in query_params:
            alertas = """
            <div class="alert alert-danger alert-dismissible fade show">
                ❌ Error en la operación
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
            """
        
        html = GESTION_TEMPLATE.format(
            usuario_actual=usuario_actual,
            gestion_actividades=gestion_actividades,
            gestion_usuarios=gestion_usuarios,
            gestion_personal=gestion_personal,
            alertas=alertas
        )
        self.servir_html(html)
    
    @medir_tiempo
    def serve_estadisticas(self, usuario_actual):
        """Sirve la página de estadísticas"""
        from database import exportar_registros_filtrados
        
        # Obtener estadísticas del usuario
        _, estadisticas = exportar_registros_filtrados(usuario=usuario_actual)
        
        html = ESTADISTICAS_TEMPLATE.format(
            usuario_actual=usuario_actual,
            total_registros=estadisticas.get('total', 0),
            por_actividad=json.dumps(estadisticas.get('por_actividad', {})),
            por_dia=json.dumps(estadisticas.get('por_dia', {}))
        )
        self.servir_html(html)
    
    @medir_tiempo
    def serve_exportar(self, usuario_actual):
        """Sirve la página de exportación"""
        try:
            from database import cargar_actividades_globales, cargar_actividades, obtener_estadisticas_exportacion
            
            parsed_path = urlparse(self.path)
            query_params = parse_qs(parsed_path.query)
            
            # Obtener todas las actividades posibles para el filtro
            actividades_globales = cargar_actividades_globales()
            actividades_personales = cargar_actividades(usuario_actual)
            todas_actividades = sorted(list(set(actividades_globales + actividades_personales)))
            
            opciones_actividades = ""
            for act in todas_actividades:
                opciones_actividades += f'<option value="{act}">{act}</option>\n'
            
            # Obtener estadísticas para los cards
            stats = obtener_estadisticas_exportacion(usuario_actual)
            
            # Manejar mensajes de error
            alertas = ""
            if 'error' in query_params:
                error_msg = query_params['error'][0]
                alertas = f'<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                          f'<i class="fas fa-exclamation-triangle"></i> {error_msg}' \
                          f'<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
            
            html = EXPORTAR_TEMPLATE.format(
                usuario_actual=usuario_actual,
                opciones_actividades=opciones_actividades,
                alertas=alertas,
                fecha_min=stats.get('fecha_min', 'N/A'),
                fecha_max=stats.get('fecha_max', 'N/A'),
                total_registros=stats.get('total_registros', 0),
                total_tipos_actividad=stats.get('total_tipos_actividad', 0),
                ultima_exportacion=stats.get('ultima_exportacion', 'Nunca')
            )
            self.servir_html(html)
            
        except Exception as e:
            print(f"Error sirviendo página de exportar: {e}")
            self.send_error(500, f"Error interno: {e}")
    
    @medir_tiempo
    def procesar_exportacion(self, form_data, usuario_actual):
        """Procesa la exportación de datos"""
        try:
            from database import exportar_registros_filtrados, generar_reporte_excel, generar_informe_template
            
            # Obtener parámetros del formulario
            fecha_inicio = form_data.get('fecha_inicio', [''])[0].strip() or None
            fecha_fin = form_data.get('fecha_fin', [''])[0].strip() or None
            actividad = form_data.get('actividad', [''])[0].strip() or None
            formato = form_data.get('formato', ['excel'])[0].strip()
            
            # Exportar registros filtrados
            df, estadisticas = exportar_registros_filtrados(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                usuario=usuario_actual,
                actividad=actividad
            )
            
            if df.empty:
                # Redirigir a exportar con mensaje de error
                self.redirect('/exportar?error=No hay datos para exportar')
                return
            
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx' if formato == 'excel' else '.csv') as tmp:
                if formato == 'excel':
                    # FORZAR el uso de la plantilla
                    success = generar_informe_template(df, tmp.name)
                    if not success:
                        # Si falla, loguear pero NO generar el excel genérico para que el usuario sepa que algo anda mal
                        print(f"ERROR: No se pudo generar el informe usando la plantilla en {tmp.name}")
                        self.redirect('/exportar?error=No se pudo cargar la plantilla Excel')
                        return
                    
                    content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    filename = f"Informe_Actividades_{usuario_actual}_{datetime.now().strftime('%Y%m%d')}.xlsx"
                else:
                    df.to_csv(tmp.name, index=False, encoding='utf-8')
                    content_type = 'text/csv'
                    filename = f"exportacion_{usuario_actual}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                # Leer el archivo
                with open(tmp.name, 'rb') as f:
                    file_data = f.read()
                
                # Limpiar archivo temporal
                os.unlink(tmp.name)
            
            # Enviar archivo como descarga
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Content-Length', str(len(file_data)))
            self.end_headers()
            self.wfile.write(file_data)
            
        except Exception as e:
            print(f"Error procesando exportación: {e}")
            self.redirect('/exportar?error=Error al procesar la exportación')
    
    # =========================================================================
    # MÉTODOS PARA PROCESAR FORMULARIOS
    # =========================================================================
    
    @medir_tiempo
    def procesar_login(self, form_data):
        """Procesa el formulario de login"""
        usuario_input = form_data.get('usuario', [''])[0].strip()
        
        if usuario_input:
            usuarios_data = cargar_usuarios()
            usuarios = usuarios_data.get('usuarios', [])
            
            # Búsqueda insensible a mayúsculas/minúsculas
            usuario_encontrado = None
            for u in usuarios:
                if u.lower() == usuario_input.lower():
                    usuario_encontrado = u
                    break
            
            if usuario_encontrado:
                self.iniciar_sesion(usuario_encontrado)
                self.redirect('/main')
                return
        
        # Login fallido
        self.redirect('/?error=1')
    
    @medir_tiempo
    def procesar_agregar_registro(self, form_data, usuario_actual):
        """Procesa el agregado de un nuevo registro"""
        try:
            ahora = datetime.now()
            
            registro = {
                'Fecha': ahora.strftime('%Y-%m-%d'),
                'Hora': ahora.strftime('%H:%M:%S'),
                'Usuario': usuario_actual,
                'Actividad': form_data.get('actividad', [''])[0],
                'Ubicacion': form_data.get('ubicacion', [''])[0],
                'TipoSolicitud': form_data.get('tipo_solicitud', [''])[0],
                'MedioSolicitud': form_data.get('medio_solicitud', [''])[0],
                'Dependencia': form_data.get('dependencia', [''])[0],
                'Solicitante': form_data.get('solicitante', [''])[0],
                'Cumplido': form_data.get('cumplido', ['Sí'])[0],
                'FechaAtencion': form_data.get('fecha_atencion', [ahora.strftime('%Y-%m-%d')])[0],
                'Observaciones': form_data.get('observaciones', [''])[0]
            }
            
            if guardar_registro(registro):
                self.redirect('/main?success=1')
            else:
                self.redirect('/main?error=1')
                
        except Exception as e:
            print(f"Error procesando registro: {e}")
            self.redirect('/main?error=1')
    
    @medir_tiempo
    def procesar_agregar_actividad_global(self, form_data):
        """Procesa agregar actividad global (solo admin)"""
        import sys
        sys.stderr.write("DEBUG: Entrando a procesar_agregar_actividad_global\n")
        try:
            nueva_actividad = form_data.get('nueva_actividad', [''])[0].strip()
            
            if nueva_actividad:
                actividades = cargar_actividades_globales()
                if nueva_actividad not in actividades:
                    actividades.append(nueva_actividad)
                    if guardar_actividades(actividades):
                        self.redirect('/gestion?success=1')
                        return
            
            self.redirect('/gestion?error=1')
        except Exception as e:
            print(f"ERROR FATAL en procesar_agregar_actividad_global: {e}")
            import traceback
            traceback.print_exc()
            self.send_error(500, f"Error interno: {e}")
    
    @medir_tiempo
    def procesar_eliminar_actividad_global(self, form_data):
        """Procesa eliminar actividad global (solo admin)"""
        actividad = form_data.get('actividad', [''])[0].strip()
        
        if actividad:
            actividades = cargar_actividades_globales()
            if actividad in actividades:
                actividades.remove(actividad)
                if guardar_actividades(actividades):
                    self.redirect('/gestion?success=1')
                    return
        
        self.redirect('/gestion?error=1')
    
    @medir_tiempo
    def procesar_agregar_actividad_personal(self, form_data, usuario_actual):
        """Procesa agregar actividad personal"""
        nueva_actividad = form_data.get('nueva_actividad', [''])[0].strip()
        
        if nueva_actividad and agregar_actividad_personal(usuario_actual, nueva_actividad):
            self.redirect('/gestion?success=1')
        else:
            self.redirect('/gestion?error=1')
    
    @medir_tiempo
    def procesar_eliminar_actividad_personal(self, form_data, usuario_actual):
        """Procesa eliminar actividad personal"""
        actividad = form_data.get('actividad', [''])[0].strip()
        
        if actividad and eliminar_actividad_personal(usuario_actual, actividad):
            self.redirect('/gestion?success=1')
        else:
            self.redirect('/gestion?error=1')
    
    @medir_tiempo
    def procesar_agregar_usuario(self, form_data):
        """Procesa agregar usuario (solo admin)"""
        nuevo_usuario = form_data.get('nuevo_usuario', [''])[0].strip()
        
        if nuevo_usuario:
            usuarios_data = cargar_usuarios()
            usuarios = usuarios_data.get('usuarios', [])
            
            if nuevo_usuario not in usuarios:
                usuarios.append(nuevo_usuario)
                usuarios_data['usuarios'] = usuarios
                
                # Inicializar actividades para el nuevo usuario
                if 'actividades' not in usuarios_data:
                    usuarios_data['actividades'] = {}
                usuarios_data['actividades'][nuevo_usuario] = []
                
                if guardar_usuarios(usuarios_data):
                    self.redirect('/gestion?success=1')
                    return
        
        self.redirect('/gestion?error=1')
    
    @medir_tiempo
    def procesar_eliminar_usuario(self, form_data):
        """Procesa eliminar usuario (solo admin)"""
        usuario = form_data.get('usuario', [''])[0].strip()
        
        if usuario and usuario != 'admin':
            usuarios_data = cargar_usuarios()
            usuarios = usuarios_data.get('usuarios', [])
            
            if usuario in usuarios:
                usuarios.remove(usuario)
                usuarios_data['usuarios'] = usuarios
                
                # Eliminar actividades del usuario
                if 'actividades' in usuarios_data and usuario in usuarios_data['actividades']:
                    del usuarios_data['actividades'][usuario]
                
                if guardar_usuarios(usuarios_data):
                    self.redirect('/gestion?success=1')
                    return
        
        self.redirect('/gestion?error=1')