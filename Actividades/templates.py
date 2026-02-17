"""
Plantillas HTML para la aplicación web.
Separadas de config.py para mantener responsabilidad única.
"""

# =============================================================================
# PLANTILLA: LOGIN
# =============================================================================

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Sistema de Actividades</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100vh; }}
        .login-container {{ max-width: 400px; margin: 100px auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    <div class="container">
        <div class="login-container">
            <h2 class="text-center mb-4">🔐 Iniciar Sesión</h2>
            {error_login}
            <form action="/login" method="POST">
                <div class="mb-3">
                    <label class="form-label">Usuario:</label>
                    <input type="text" name="usuario" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-primary w-100">🚀 Ingresar</button>
            </form>
            <div class="mt-3 text-center">
                <small class="text-muted">Usa cualquier usuario existente o crea uno nuevo</small>
            </div>
        </div>
    </div>
</body>
</html>
"""

# =============================================================================
# ESTILOS COMPARTIDOS (usados en varias plantillas)
# =============================================================================

_SHARED_STYLES = """
    .navbar-custom {{ background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
    .sidebar {{ background: #f8f9fa; border-right: 1px solid #dee2e6; height: 100vh; position: fixed; width: 250px; z-index: 1000; }}
    .main-content {{ margin-left: 250px; padding: 30px; background: #f0f2f5; min-height: calc(100vh - 56px); }}
    .card {{ border: none; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); margin-bottom: 25px; transition: transform 0.3s; }}
    .card-header {{ background: white; border-bottom: 1px solid #f0f0f0; border-radius: 15px 15px 0 0 !important; padding: 15px 20px; }}
    .card-header h5 {{ margin: 0; color: #4a5568; font-weight: 700; }}
    .btn-action {{ border-radius: 8px; padding: 8px 16px; font-weight: 600; }}
    .form-control {{ border-radius: 10px; padding: 12px; border: 1px solid #e2e8f0; }}
    .form-control:focus {{ box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); border-color: #667eea; }}
"""

_SIDEBAR_TEMPLATE = """
    <div class="col-md-2 sidebar d-none d-md-block">
        <div class="pt-4">
            <div class="list-group list-group-flush">
                <a href="/" class="list-group-item list-group-item-action {active_inicio}">
                    <i class="fas fa-home me-2 text-primary"></i> Inicio
                </a>
                <a href="/gestion" class="list-group-item list-group-item-action {active_gestion}">
                    <i class="fas fa-cog me-2 text-primary"></i> Mi Gestión
                </a>
                <a href="/estadisticas" class="list-group-item list-group-item-action {active_estadisticas}">
                    <i class="fas fa-chart-line me-2 text-primary"></i> Estadísticas
                </a>
                <a href="/exportar" class="list-group-item list-group-item-action {active_exportar}">
                    <i class="fas fa-file-export me-2 text-primary"></i> Exportar
                </a>
            </div>
        </div>
    </div>
"""

_NAVBAR_TEMPLATE = """
    <nav class="navbar navbar-expand-lg navbar-dark navbar-custom sticky-top">
        <div class="container-fluid">
            <span class="navbar-brand fw-bold mb-0">
                <i class="fas fa-{icono} me-2"></i> {titulo}
            </span>
            <div class="ms-auto d-flex align-items-center">
                <span class="badge bg-white text-dark py-2 px-3 rounded-pill me-3 shadow-sm">
                    <i class="fas fa-user-circle me-1 text-primary"></i> {usuario_actual}
                </span>
                <a class="btn btn-sm btn-outline-light px-3 rounded-pill me-2" href="/">
                    <i class="fas fa-home me-1"></i> Inicio
                </a>
                <a class="btn btn-sm btn-outline-light px-3 rounded-pill" href="/logout">
                    <i class="fas fa-sign-out-alt me-1"></i> Salir
                </a>
            </div>
        </div>
    </nav>
"""

# =============================================================================
# PLANTILLA: PÁGINA PRINCIPAL
# =============================================================================

MAIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Actividades</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        """ + _SHARED_STYLES + """
        .btn-small {{ padding: 0.25rem 0.5rem; font-size: 0.875rem; }}
        .stat-card {{ background: white; border-radius: 10px; padding: 20px; margin: 10px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    """ + _NAVBAR_TEMPLATE.replace("{icono}", "tasks").replace("{titulo}", "Sistema de Actividades") + """

    <div class="container-fluid p-0">
        <div class="row g-0">
            """ + _SIDEBAR_TEMPLATE.format(active_inicio="active", active_gestion="", active_estadisticas="", active_exportar="") + """

            <div class="col-md-10 main-content">
                <div class="container-fluid">
                    {alertas}

                    <h2 class="mb-4"><i class="fas fa-plus-circle"></i> Nuevo Registro</h2>
                    
                    <form action="/agregar_registro" method="POST">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">📝 Actividad:</label>
                                    <select name="actividad" class="form-select" required>
                                        <option value="">Seleccionar actividad...</option>
                                        {opciones_actividades}
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">📍 Ubicación:</label>
                                    <select name="ubicacion" class="form-select" required>
                                        <option value="">Seleccionar ubicación...</option>
                                        {opciones_ubicaciones}
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">🔧 Tipo de Solicitud:</label>
                                    <select name="tipo_solicitud" class="form-select" required>
                                        <option value="">Seleccionar tipo...</option>
                                        {opciones_tipos}
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">👤 Solicitante:</label>
                                    <input type="text" name="solicitante" class="form-control" placeholder="Nombre de quien solicita" required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-4">
                                    <label class="form-label">📞 Medio de Solicitud:</label>
                                    <select name="medio_solicitud" class="form-select" required>
                                        <option value="">Seleccionar medio...</option>
                                        {opciones_medios}
                                    </select>
                                </div>
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">✅ Cumplido:</label>
                                            <select name="cumplido" class="form-select">
                                                <option value="Sí">Sí</option>
                                                <option value="No">No</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">📅 Fecha Atención:</label>
                                            <input type="date" name="fecha_atencion" class="form-control" value="{fecha_hoy}">
                                        </div>
                                    </div>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">📋 Observaciones:</label>
                                    <textarea name="observaciones" class="form-control" rows="2" placeholder="Detalles adicionales..."></textarea>
                                </div>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary btn-lg">
                            <i class="fas fa-save"></i> Guardar Registro
                        </button>
                    </form>
                    
                    <hr class="my-5">
                    
                    <h3 class="mb-3"><i class="fas fa-history"></i> Registros Recientes</h3>
                    <div class="table-responsive">
                        <table class="table table-hover align-middle">
                            <thead class="table-light">
                                <tr>
                                    <th>Fecha</th>
                                    <th>Hora</th>
                                    <th>Actividad</th>
                                    <th>Ubicación</th>
                                    <th>Tipo</th>
                                    <th>Cumplido</th>
                                    <th class="text-end">Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {tabla_registros}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# =============================================================================
# PLANTILLA: GESTIÓN
# =============================================================================

GESTION_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestión - Sistema de Actividades</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        """ + _SHARED_STYLES + """
        .list-group-item {{ border: none; border-bottom: 1px solid #f8f9fa; padding: 15px 20px; transition: background 0.2s; }}
        .list-group-item:hover {{ background: #f8fafc; }}
        .list-group-item:last-child {{ border-bottom: none; }}
        .badge-user {{ background: #ebf4ff; color: #3182ce; padding: 8px 12px; border-radius: 8px; font-weight: 600; }}
    </style>
</head>
<body>
    """ + _NAVBAR_TEMPLATE.replace("{icono}", "cog").replace("{titulo}", "Panel de Configuración") + """

    <div class="container-fluid p-0">
        <div class="row g-0">
            """ + _SIDEBAR_TEMPLATE.format(active_inicio="", active_gestion="active", active_estadisticas="", active_exportar="") + """

            <div class="col-md-10 main-content">
                <div class="container-fluid">
                    {alertas}

                    <div class="row">
                        <div class="col-lg-7">
                            <div class="card">
                                <div class="card-header d-flex justify-content-between align-items-center">
                                    <h5><i class="fas fa-tasks text-primary me-2"></i> Gestión de Actividades</h5>
                                </div>
                                <div class="card-body">
                                    {gestion_actividades}
                                    <div class="mt-4">
                                        {gestion_personal}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="col-lg-5">
                            <div class="card">
                                <div class="card-header">
                                    <h5><i class="fas fa-users-cog text-primary me-2"></i> Usuarios del Sistema</h5>
                                </div>
                                <div class="card-body">
                                    {gestion_usuarios}
                                </div>
                            </div>

                            <div class="card bg-gradient-primary text-white" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                                <div class="card-body text-center py-4">
                                    <i class="fas fa-info-circle fa-3x mb-3 opacity-50"></i>
                                    <h5>Ayuda del Sistema</h5>
                                    <p class="small mb-0">Recuerda que los cambios en actividades globales afectan a todos los usuarios. Las actividades personales son privadas para cada cuenta.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# =============================================================================
# PLANTILLA: ESTADÍSTICAS
# =============================================================================

ESTADISTICAS_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Estadísticas - Sistema de Actividades</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        """ + _SHARED_STYLES + """
        .stat-card {{ border: none; border-radius: 15px; background: white; padding: 25px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); transition: transform 0.3s; height: 100%; }}
        .stat-card:hover {{ transform: translateY(-5px); }}
        .stat-icon {{ width: 50px; height: 50px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 15px; font-size: 20px; }}
        .icon-blue {{ background: #ebf4ff; color: #3182ce; }}
        .icon-green {{ background: #f0fff4; color: #38a169; }}
        .icon-orange {{ background: #fffaf0; color: #dd6b20; }}
        .icon-purple {{ background: #faf5ff; color: #805ad5; }}
        .stat-value {{ font-size: 1.8rem; font-weight: 800; color: #2d3748; }}
        .stat-label {{ color: #718096; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; font-size: 0.75rem; }}
        .chart-container {{ background: white; border-radius: 15px; padding: 25px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); margin-bottom: 30px; }}
        .chart-title {{ font-weight: 700; color: #1a202c; margin-bottom: 20px; border-left: 4px solid #667eea; padding-left: 15px; }}
    </style>
</head>
<body>
    """ + _NAVBAR_TEMPLATE.replace("{icono}", "chart-bar").replace("{titulo}", "Dashboard de Rendimiento") + """

    <div class="container-fluid p-0">
        <div class="row g-0">
            """ + _SIDEBAR_TEMPLATE.format(active_inicio="", active_gestion="", active_estadisticas="active", active_exportar="") + """

            <div class="col-md-10 main-content">
                <div class="row g-4 mb-4">
                    <div class="col-12">
                        <div class="card border-0 shadow-sm rounded-4">
                            <div class="card-body p-4">
                                <form action="/estadisticas" method="GET" class="row align-items-end g-3">
                                    <div class="col-md-4">
                                        <label class="form-label small fw-bold text-muted">FECHA INICIO</label>
                                        <input type="date" name="fecha_inicio" class="form-control" value="{val_fecha_inicio}">
                                    </div>
                                    <div class="col-md-4">
                                        <label class="form-label small fw-bold text-muted">FECHA FIN</label>
                                        <input type="date" name="fecha_fin" class="form-control" value="{val_fecha_fin}">
                                    </div>
                                    <div class="col-md-2">
                                        <button type="submit" class="btn btn-primary w-100 py-2">
                                            <i class="fas fa-filter"></i> Filtrar
                                        </button>
                                    </div>
                                    <div class="col-md-2">
                                        <a href="/estadisticas" class="btn btn-outline-secondary w-100 py-2">
                                            <i class="fas fa-undo"></i> Limpiar
                                        </a>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row g-4 mb-5">
                    <div class="col-md-3">
                        <div class="stat-card">
                            <div class="stat-icon icon-blue"><i class="fas fa-database"></i></div>
                            <div class="stat-value">{total_registros}</div>
                            <div class="stat-label">Registros</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card">
                            <div class="stat-icon icon-green"><i class="fas fa-check-double"></i></div>
                            <div class="stat-value">{total_tipos_actividad}</div>
                            <div class="stat-label">Tipo Actividades</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card">
                            <div class="stat-icon icon-orange"><i class="fas fa-tachometer-alt"></i></div>
                            <div class="stat-value">{promedio_diario}</div>
                            <div class="stat-label">Promedio Diario</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card">
                            <div class="stat-icon icon-purple"><i class="fas fa-calendar-alt"></i></div>
                            <div class="stat-value h5 mb-0" style="padding-top: 10px;">{fecha_min}</div>
                            <div class="stat-label">Desde</div>
                        </div>
                    </div>
                </div>

                <div class="row">
                    <div class="col-lg-8"> 
                        <div class="card border-0 shadow-sm rounded-4 mb-4">
                            <div class="card-header bg-white py-3">
                                <h5 class="mb-0"><i class="fas fa-users me-2 text-primary"></i> Resumen por Ejecutivo</h5>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-sm table-hover mb-0">
                                        <thead>
                                            <tr class="text-muted small text-uppercase">
                                                <th>Usuario</th>
                                                <th class="text-center">Total</th>
                                                <th class="text-center">Cumplido %</th>
                                                <th>Última Actividad</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {tabla_usuarios_stats}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>

                        <div class="chart-container">
                            <h5 class="chart-title">Tendencia de Registros Diarios</h5>
                            <div style="position: relative; height: 350px;">
                                <canvas id="lineaChart"></canvas>
                            </div>
                        </div>
                    </div>
                    <div class="col-lg-4">
                        <div class="chart-container">
                            <h5 class="chart-title">Nivel de Cumplimiento</h5>
                            <div style="position: relative; height: 350px;">
                                <canvas id="cumplimientoChart"></canvas>
                            </div>
                        </div>
                        <div class="card border-0 shadow-sm rounded-4 overflow-hidden mt-4">
                            <div class="card-body p-4 bg-primary text-white">
                                <h6 class="fw-bold mb-3"><i class="fas fa-lightbulb me-2"></i> Dato Curioso</h6>
                                <p class="small mb-0 opacity-75">El sistema ha procesado {total_registros} registros hasta el momento. ¡Sigue así!</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const dataActividades = {data_actividades};
        const dataCumplimiento = {data_cumplimiento};
        const dataLinea = {data_linea};
        const colors = ['#667eea', '#764ba2', '#38a169', '#3182ce', '#dd6b20', '#805ad5', '#e53e3e', '#319795', '#d69e2e', '#4a5568'];

        new Chart(document.getElementById('actividadesChart'), {{
            type: 'bar',
            data: {{ labels: dataActividades.labels, datasets: [{{ label: 'Registros', data: dataActividades.data, backgroundColor: colors[0], borderRadius: 8 }}] }},
            options: {{ indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
        }});

        new Chart(document.getElementById('cumplimientoChart'), {{
            type: 'doughnut',
            data: {{ labels: dataCumplimiento.labels, datasets: [{{ data: dataCumplimiento.data, backgroundColor: ['#38a169', '#e53e3e', '#dd6b20'] }}] }},
            options: {{ responsive: true, cutout: '70%', plugins: {{ legend: {{ position: 'bottom' }} }} }}
        }});

        new Chart(document.getElementById('lineaChart'), {{
            type: 'line',
            data: {{ labels: dataLinea.labels, datasets: [{{ label: 'Registros', data: dataLinea.data, borderColor: colors[1], backgroundColor: colors[1] + '20', fill: true, tension: 0.4, pointRadius: 4, pointBackgroundColor: colors[1] }}] }},
            options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ beginAtZero: true, ticks: {{ stepSize: 1 }} }} }} }}
        }});
    </script>
</body>
</html>
"""

# =============================================================================
# PLANTILLA: EXPORTAR
# =============================================================================

EXPORTAR_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Exportar - Sistema de Actividades</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        """ + _SHARED_STYLES + """
        .stats-card {{ border-left: 4px solid #007bff; }}
        .stats-card.success {{ border-left-color: #28a745; }}
        .stats-card.warning {{ border-left-color: #ffc107; }}
        .stats-card.info {{ border-left-color: #17a2b8; }}
    </style>
</head>
<body>
    """ + _NAVBAR_TEMPLATE.replace("{icono}", "download").replace("{titulo}", "Exportar Datos") + """

    <div class="container-fluid p-0">
        <div class="row g-0">
            """ + _SIDEBAR_TEMPLATE.format(active_inicio="", active_gestion="", active_estadisticas="", active_exportar="active") + """

            <div class="col-md-10 main-content">
                <h2 class="mb-4"><i class="fas fa-download"></i> Exportar Datos</h2>
                
                {alertas}

                <div class="card mb-4">
                    <div class="card-header">
                        <h5><i class="fas fa-filter"></i> Filtros de Exportación</h5>
                    </div>
                    <div class="card-body">
                        <form method="POST" action="/exportar">
                            <div class="row">
                                <div class="col-md-3">
                                    <div class="mb-3">
                                        <label class="form-label">Fecha Inicio</label>
                                        <input type="date" class="form-control" name="fecha_inicio">
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="mb-3">
                                        <label class="form-label">Fecha Fin</label>
                                        <input type="date" class="form-control" name="fecha_fin">
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="mb-3">
                                        <label class="form-label">Tipo de Actividad</label>
                                        <select class="form-select" name="actividad">
                                            <option value="Todas">Todas las actividades</option>
                                            {opciones_actividades}
                                         </select>
                                    </div>
                                </div>
                                {filtro_usuario_html}
                                <div class="col-md-3">
                                    <div class="mb-3">
                                        <label class="form-label">Formato</label>
                                        <select class="form-select" name="formato">
                                            <option value="excel">Excel (.xlsx)</option>
                                            <option value="csv">CSV (.csv)</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="mb-3">
                                        <label class="form-label">Tipo de Reporte</label>
                                        <select class="form-select" name="tipo_reporte">
                                            <option value="detallado">Detallado (Plantilla Base)</option>
                                            <option value="final">Informe Final (Concentrado)</option>
                                        </select>
                                    </div>
                                </div>
                            </div>

                            <div class="row border-top pt-4 mt-2">
                                <div class="col-12 mb-3">
                                    <h6 class="text-muted text-uppercase small fw-bold"><i class="fas fa-file-signature me-2"></i> Datos del Contrato</h6>
                                </div>
                                <div class="col-md-8">
                                    <div class="mb-3">
                                        <label class="form-label">Objeto del Contrato</label>
                                        <textarea class="form-control" name="contrato_objeto" rows="2" placeholder="Describa el objeto del contrato...">{val_contrato_objeto}</textarea>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label class="form-label">Nro. Contrato</label>
                                        <input type="text" class="form-control" name="contrato_nro" placeholder="Ej: 123-2024" value="{val_contrato_nro}">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">Nombre del Contratista</label>
                                        <input type="text" class="form-control" name="contrato_nombre" placeholder="Nombre completo" value="{val_contrato_nombre}">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">Cédula / NIT</label>
                                        <input type="text" class="form-control" name="contrato_cedula" placeholder="Documento de identidad" value="{val_contrato_cedula}">
                                    </div>
                                </div>
                                <div class="col-12">
                                    <div class="mb-3">
                                        <label class="form-label">Supervisor del Contrato</label>
                                        <input type="text" class="form-control" name="contrato_supervisor" placeholder="Nombre del supervisor" value="{val_contrato_supervisor}">
                                    </div>
                                </div>
                            </div>
                            <div class="text-center">
                                <button type="submit" class="btn btn-primary">
                                    <i class="fas fa-file-excel"></i> 🚀 Generar Informe (V2 ACTUALIZADO)
                                </button>
                            </div>
                        </form>
                    </div>
                </div>

                <div class="row mb-4">
                    <div class="col-md-3">
                        <div class="card stats-card">
                            <div class="card-body text-center">
                                <i class="fas fa-calendar fa-2x text-primary mb-2"></i>
                                <h5>Rango de Fechas</h5>
                                <p class="text-muted">{fecha_min} - {fecha_max}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card stats-card success">
                            <div class="card-body text-center">
                                <i class="fas fa-list-alt fa-2x text-success mb-2"></i>
                                <h5>Total Registros</h5>
                                <p class="text-muted">{total_registros} registros</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card stats-card warning">
                            <div class="card-body text-center">
                                <i class="fas fa-tasks fa-2x text-warning mb-2"></i>
                                <h5>Tipos de Actividad</h5>
                                <p class="text-muted">{total_tipos_actividad} tipos</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card stats-card info">
                            <div class="card-body text-center">
                                <i class="fas fa-history fa-2x text-info mb-2"></i>
                                <h5>Última Exportación</h5>
                                <p class="text-muted">{ultima_exportacion}</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i> 
                    <strong>Características de la exportación:</strong>
                    <ul class="mb-0 mt-2">
                        <li>Filtrado por rangos de fechas</li>
                        <li>Organización por actividad y fecha</li>
                        <li>Conteo de actividades por tipo</li>
                        <li>Estadísticas detalladas incluidas</li>
                        <li>Formatos disponibles: Excel y CSV</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
