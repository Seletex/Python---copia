"""
Módulo de utilidades HTML para generar opciones de selects y formularios.
Solo genera fragmentos HTML, no páginas completas.
"""

from database import (
    cargar_actividades, cargar_actividades_globales, cargar_ubicaciones, 
    cargar_tipos_solicitud, cargar_medios_solicitud, cargar_usuarios
)
from activity_service import obtener_actividades_personales
from utils import medir_tiempo

# =============================================================================
# GENERACIÓN DE OPTIONS PARA SELECTS
# =============================================================================

def _generar_opciones(items, truncar=False, max_len=80):
    """Helper genérico para generar <option> HTML"""
    opciones = ""
    for item in items:
        display = item if not truncar or len(item) <= max_len else item[:max_len-3] + "..."
        opciones += f'<option value="{item}" title="{item}">{display}</option>\n'
    return opciones

@medir_tiempo
def generar_opciones_actividades(usuario=None):
    """Genera opciones para el select de actividades"""
    return _generar_opciones(cargar_actividades(usuario), truncar=True)

@medir_tiempo
def generar_opciones_ubicaciones():
    """Genera opciones para el select de ubicaciones"""
    return _generar_opciones(cargar_ubicaciones())

@medir_tiempo
def generar_opciones_tipos_solicitud():
    """Genera opciones para el select de tipos de solicitud"""
    return _generar_opciones(cargar_tipos_solicitud())

@medir_tiempo
def generar_opciones_medios_solicitud():
    """Genera opciones para el select de medios de solicitud"""
    return _generar_opciones(cargar_medios_solicitud())

@medir_tiempo
def generar_opciones_usuarios():
    """Genera opciones para el select de usuarios"""
    usuarios = cargar_usuarios().get("usuarios", [])
    return _generar_opciones(usuarios)

# =============================================================================
# GENERACIÓN DE INTERFACES DE GESTIÓN
# =============================================================================

@medir_tiempo
def generar_gestion_actividades_globales():
    """Genera HTML para la gestión de actividades globales (solo admin)"""
    return _generar_gestion_lista_simple(
        titulo="🎨 Actividades Globales",
        item_label="actividad global",
        items=cargar_actividades_globales(),
        action_add="/agregar_actividad_global",
        action_del="/eliminar_actividad_global",
        field_name="actividad"
    )

@medir_tiempo
def generar_gestion_ubicaciones():
    """Genera HTML para la gestión de ubicaciones"""
    return _generar_gestion_lista_simple(
        titulo="📍 Gestión de Ubicaciones",
        item_label="ubicación",
        items=cargar_ubicaciones(),
        action_add="/agregar_ubicacion",
        action_del="/eliminar_ubicacion",
        field_name="ubicacion"
    )

@medir_tiempo
def generar_gestion_tipos_solicitud():
    """Genera HTML para la gestión de tipos de solicitud"""
    return _generar_gestion_lista_simple(
        titulo="📝 Tipos de Solicitud",
        item_label="tipo de solicitud",
        items=cargar_tipos_solicitud(),
        action_add="/agregar_tipo_solicitud",
        action_del="/eliminar_tipo_solicitud",
        field_name="tipo"
    )

@medir_tiempo
def generar_gestion_medios_solicitud():
    """Genera HTML para la gestión de medios de solicitud"""
    return _generar_gestion_lista_simple(
        titulo="📞 Medios de Solicitud",
        item_label="medio de solicitud",
        items=cargar_medios_solicitud(),
        action_add="/agregar_medio_solicitud",
        action_del="/eliminar_medio_solicitud",
        field_name="medio"
    )

def _generar_gestion_lista_simple(titulo, item_label, items, action_add, action_del, field_name):
    """Helper genérico para generar una sección de gestión de lista (Añadir/Eliminar)"""
    id_prefix = action_add.strip('/').replace('_', '-')
    contenido = f"""
    <div class="mb-5 p-4 border rounded-3 bg-white shadow-sm">
        <h6 class="text-uppercase text-primary fw-bold mb-3 small d-flex align-items-center">
            {titulo}
        </h6>
        <form action="{action_add}" method="POST" class="row g-2 mb-4">
            <div class="col-md-9">
                <input type="text" name="nuevo_item" 
                       placeholder="Añadir {item_label}..." class="form-control" required>
            </div>
            <div class="col-md-3">
                <button type="submit" class="btn btn-primary w-100">
                    <i class="fas fa-plus me-2"></i>Añadir
                </button>
            </div>
        </form>
        <div class="list-group list-group-flush border-top">
    """
    
    if items:
        for item in items:
            contenido += f"""
            <div class="list-group-item d-flex justify-content-between align-items-center py-3 px-2 border-bottom">
                <div class="text-dark small"><i class="fas fa-chevron-right me-3 text-muted opacity-50"></i>{item}</div>
                <form action="{action_del}" method="POST" class="ms-2">
                    <input type="hidden" name="{field_name}" value="{item}">
                    <button type="submit" class="btn btn-outline-danger btn-sm border-0" 
                            onclick="return confirm('¿Eliminar esta {item_label}?')">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </form>
            </div>
            """
    else:
        contenido += f"""
            <div class="list-group-item text-center text-muted py-4">
                No hay {item_label} configuradas
            </div>
        """
    
    contenido += "</div></div>"
    return contenido


@medir_tiempo
def generar_gestion_usuarios(usuario_actual):
    """Genera HTML para la gestión de usuarios"""
    usuarios = cargar_usuarios().get("usuarios", [])
    
    if usuario_actual != "admin":
        return """
        <div class='text-center py-5'>
            <i class='fas fa-lock fa-3x text-muted mb-3 opacity-25'></i>
            <p class='text-muted'>Solo administradores pueden gestionar usuarios.</p>
        </div>
        """
    
    contenido = """
    <div class="mb-4">
        <h6 class="text-uppercase text-muted fw-bold mb-3 small">➕ Registro de Usuarios</h6>
        <form action="/agregar_usuario" method="POST" class="mb-4">
            <div class="input-group">
                <span class="input-group-text bg-white border-end-0"><i class="fas fa-user text-muted"></i></span>
                <input type="text" name="nuevo_usuario" class="form-control border-start-0" 
                       placeholder="Ej: nombre.apellido" required>
                <button type="submit" class="btn btn-success">Añadir</button>
            </div>
        </form>
        <h6 class="text-uppercase text-muted fw-bold mb-3 small">👥 Usuarios Registrados</h6>
        <div class="list-group shadow-sm">
    """
    
    for usuario in usuarios:
        is_admin = usuario == "admin"
        badge = '<span class="badge bg-warning text-dark small">Administrador</span>' if is_admin else '<span class="text-muted small">Usuario Estándar</span>'
        delete_btn = "" if is_admin else f'''
            <form action="/eliminar_usuario" method="POST">
                <input type="hidden" name="usuario" value="{usuario}">
                <button type="submit" class="btn btn-outline-danger btn-sm border-0" 
                        onclick="return confirm('¿Eliminar al usuario {usuario}?')">
                    <i class="fas fa-user-minus"></i>
                </button>
            </form>
        '''
        contenido += f"""
        <div class="list-group-item d-flex justify-content-between align-items-center py-3">
            <div class="d-flex align-items-center">
                <div class="rounded-circle bg-light p-2 me-3">
                    <i class="fas fa-user-circle text-primary"></i>
                </div>
                <div>
                    <div class="fw-bold text-dark">{usuario}</div>
                    {badge}
                </div>
            </div>
            {delete_btn}
        </div>
        """
    
    contenido += "</div></div>"
    return contenido


@medir_tiempo
def generar_gestion_actividades_personales(usuario_actual):
    """Genera HTML para gestión de actividades personales"""
    if not usuario_actual or usuario_actual == "admin":
        return ""
    
    try:
        actividades_personales = obtener_actividades_personales(usuario_actual)
        
        contenido = f"""
        <div class="mb-4">
            <h6 class="text-uppercase text-muted fw-bold mb-3 small">✨ Mis Actividades Propias</h6>
            <form action="/agregar_actividad_personal" method="POST" class="row g-2 mb-4">
                <input type="hidden" name="usuario" value="{usuario_actual}">
                <div class="col-md-9">
                    <input type="text" name="nueva_actividad" 
                           placeholder="Agrega algo específico de tu cargo..." class="form-control" required>
                </div>
                <div class="col-md-3">
                    <button type="submit" class="btn btn-outline-primary w-100">Añadir</button>
                </div>
            </form>
            <div class="list-group shadow-sm rounded-3">
        """
        
        if actividades_personales:
            for actividad in actividades_personales:
                contenido += f"""
                <div class="list-group-item d-flex justify-content-between align-items-center py-3">
                    <div class="text-dark small"><i class="fas fa-user-tag me-2 text-info"></i>{actividad}</div>
                    <form action="/eliminar_actividad_personal" method="POST">
                        <input type="hidden" name="usuario" value="{usuario_actual}">
                        <input type="hidden" name="actividad" value="{actividad}">
                        <button type="submit" class="btn btn-link text-danger p-0 ms-2" 
                                onclick="return confirm('¿Eliminar actividad personal?')">
                            <i class="fas fa-times"></i>
                        </button>
                    </form>
                </div>
                """
        else:
            contenido += """
                <div class="list-group-item text-center text-muted py-4 border-dashed" 
                     style="border: 2px dashed #e2e8f0; background: #f8fafc;">
                    No tienes actividades personales.
                </div>
            """
        
        contenido += "</div></div>"
        return contenido
    except Exception as e:
        return "<div class='alert alert-danger'>Error cargando actividades personales</div>"


@medir_tiempo
def generar_tabla_registros_recientes(df, usuario_actual):
    """Genera el HTML para la tabla de registros recientes con acciones"""
    if df.empty:
        return '<tr><td colspan="7" class="text-center text-muted">No hay registros recientes</td></tr>'
    
    # Tomar los últimos 10
    df_recientes = df.tail(10).iloc[::-1]
    
    html = ""
    for _, row in df_recientes.iterrows():
        id_reg = row.get('ID', '')
        es_propietario = (row.get('USUARIO') == usuario_actual) or (usuario_actual == "admin")
        
        acciones = ""
        if es_propietario:
            acciones = f"""
                <form action="/eliminar_registro_accion" method="POST" style="display:inline;" onsubmit="return confirm('¿Eliminar este registro?')">
                    <input type="hidden" name="id_registro" value="{id_reg}">
                    <button type="submit" class="btn btn-sm btn-outline-danger border-0">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </form>
            """
        
        html += f"""
        <tr>
            <td>{str(row.get('FECHA', ''))[:10]}</td>
            <td>{str(row.get('FECHA', ''))[11:16]}</td>
            <td title="{row.get('TIPO DE ACTIVIDAD', '')}">{str(row.get('TIPO DE ACTIVIDAD', ''))[:40]}...</td>
            <td>{row.get('DEPENDENCIA', '')}</td>
            <td>{row.get('TIPO DE SOLICITUD', '')}</td>
            <td>{row.get('CUMPLIDO', '')}</td>
            <td class="text-end">{acciones}</td>
        </tr>
        """
    return html