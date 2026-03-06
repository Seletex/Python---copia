"""
Aplicación Web de Gestión de Actividades
Versión Refactorizada: Arquitectura Modular basada en Controladores

Arquitectura:
  config.py          → Constantes y logging
  templates.py       → Plantillas HTML
  database.py        → Inicialización y CRUD básico
  activity_service.py → Actividades personales
  export_service.py  → Exportación y reportes
  html_utils.py      → Generación de fragmentos HTML
  web_handlers.py    → Controladores de rutas
  utils.py           → Decoradores y cache
  app_web.py         → Este archivo (servidor HTTP)
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from config import logger
from database import inicializar_config, inicializar_excel, inicializar_usuarios
from web_handlers import ROUTE_MAP


class RequestHandler(BaseHTTPRequestHandler):
    """
    Handler HTTP principal.
    Actúa como enrutador delegando la lógica a clases en web_handlers.py.
    """
    
    def do_GET(self):
        self._dispatch('get')

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ""
        self._dispatch('post', post_data)

    def _dispatch(self, method, post_data=None):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        params = parse_qs(parsed_path.query)

        try:
            handler_class = ROUTE_MAP.get(path)
            
            if handler_class:
                handler = handler_class(self)
                if method == 'get':
                    handler.get(params)
                else:
                    handler.post(params, post_data)
            else:
                self.send_error(404, "Página no encontrada")
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error catastrófico procesando {method.upper()} {path}: {e}\n{error_details}")
            
            # Intentar enviar una respuesta de error amigable al cliente
            try:
                self.send_response(500)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                error_html = f"""
                <html>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: #dc3545;">⚠️ Ups! Algo salió mal</h1>
                    <p>Ha ocurrido un error interno en el servidor.</p>
                    <p style="color: #6c757d;">El error ha sido registrado y estamos trabajando para solucionarlo.</p>
                    <a href="/" style="display: inline-block; margin-top: 20px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">Volver al inicio</a>
                </body>
                </html>
                """
                self.wfile.write(error_html.encode('utf-8'))
            except:
                # Si esto también falla, al menos el logger ya registró el error original
                pass

    def log_message(self, format, *args):
        """Silenciar logs estándar, usamos logger personalizado"""
        pass


if __name__ == "__main__":
    inicializar_usuarios()
    inicializar_config()
    inicializar_excel()
    
    PORT = 8000
    
    print("=" * 60)
    print("GESTORES DE ACTIVIDADES - VERSION MODULAR")
    print("=" * 60)
    print(f"\nServidor iniciado en: http://localhost:{PORT}")
    print("\nAbre tu navegador y ve a: http://localhost:8000")
    print("\nPresiona Ctrl+C para detener el servidor\n")
    print("=" * 60)
    
    server = HTTPServer(('localhost', PORT), RequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✅ Servidor detenido correctamente")
        server.shutdown()
