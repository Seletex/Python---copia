"""Interfaz de usuario de la aplicación de actividades.

Este archivo contiene la interfaz gráfica principal y reutiliza
las utilidades de datos definidas en `data_utils.py`.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import pandas as pd
from datetime import datetime

# Importar utilidades de datos externalizadas
from data_utils import *

# Intentar importar FPDF solo si se desea habilitar PDF
PDF_AVAILABLE = False
if PDF_AVAILABLE:
    try:
        from fpdf import FPDF
    except Exception:
        PDF_AVAILABLE = False

# ==================== FUNCIONES DE USUARIO ====================

def mostrar_login(root, callback):
    """Muestra la ventana de login para seleccionar usuario"""
    login_window = tk.Toplevel(root)
    login_window.title("🔐 Seleccionar Usuario")
    login_window.geometry("400x300")
    login_window.transient(root)
    login_window.grab_set()
    login_window.resizable(False, False)
    
    # Centrar ventana
    login_window.update_idletasks()
    x = (login_window.winfo_screenwidth() // 2) - (400 // 2)
    y = (login_window.winfo_screenheight() // 2) - (300 // 2)
    login_window.geometry(f"400x300+{x}+{y}")
    
    ttk.Label(login_window, text="👤 Seleccione su usuario", 
             font=("Arial", 14, "bold")).pack(pady=20)
    
    # Frame para la lista de usuarios
    frame_lista = ttk.Frame(login_window)
    frame_lista.pack(fill="both", expand=True, padx=20, pady=10)
    
    # Obtener lista de usuarios
    usuarios_data = cargar_usuarios()
    usuarios = usuarios_data.get("usuarios", ["admin"])
    
    # Lista de usuarios
    lista_usuarios = tk.Listbox(frame_lista, height=8, font=("Arial", 12))
    scrollbar = ttk.Scrollbar(frame_lista, orient="vertical", command=lista_usuarios.yview)
    lista_usuarios.configure(yscrollcommand=scrollbar.set)
    
    for usuario in usuarios:
        lista_usuarios.insert(tk.END, usuario)
    
    lista_usuarios.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Botón para seleccionar
    def seleccionar_usuario():
        seleccion = lista_usuarios.curselection()
        if seleccion:
            usuario_seleccionado = lista_usuarios.get(seleccion[0])
            callback(usuario_seleccionado)
            login_window.destroy()
        else:
            messagebox.showwarning("Selección", "Por favor seleccione un usuario")
    
    ttk.Button(login_window, text="🚀 Ingresar", command=seleccionar_usuario).pack(pady=10)
    
    # Permitir doble click para ingresar
    lista_usuarios.bind("<Double-1>", lambda e: seleccionar_usuario())
    
    # Centrar el foco en la lista
    lista_usuarios.focus_set()
    if usuarios:
        lista_usuarios.selection_set(0)

# ==================== CLASE PRINCIPAL ====================

class AplicacionActividades:
    def __init__(self, root, usuario_actual):
        self.root = root
        self.usuario_actual = usuario_actual
        self.root.title(f"📋 Gestor de Actividades - Usuario: {usuario_actual}")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f0f0f0")

        # Variables de estado
        self.registro_seleccionado = None
        
        # Inicializar archivos
        inicializar_config()
        inicializar_usuarios()
        inicializar_excel()

        # Cargar opciones desde config
        self.cargar_opciones_desde_config()
        
        # Crear interfaz
        self.crear_interfaz()
        
        # Cargar datos iniciales
        self.actualizar_tabla()
        self.actualizar_listas_config()

    def actualizar_lista_usuarios(self):
        """Actualiza la lista de usuarios en la interfaz"""
        self.lista_usuarios.delete(0, tk.END)
        usuarios_data = cargar_usuarios()
        usuarios = usuarios_data.get("usuarios", [])
        
        for usuario in usuarios:
            self.lista_usuarios.insert(tk.END, usuario)

    def agregar_usuario(self):
        """Agrega un nuevo usuario"""
        nuevo_usuario = self.entry_nuevo_usuario.get().strip()
        
        if not nuevo_usuario:
            messagebox.showwarning("Validación", "El nombre de usuario no puede estar vacío")
            return
        
        usuarios_data = cargar_usuarios()
        usuarios = usuarios_data.get("usuarios", [])
        
        if nuevo_usuario in usuarios:
            messagebox.showwarning("Duplicado", f"El usuario '{nuevo_usuario}' ya existe")
            return
        
        usuarios.append(nuevo_usuario)
        usuarios_data["usuarios"] = usuarios
        
        if guardar_usuarios(usuarios_data):
            messagebox.showinfo("Éxito", f"Usuario '{nuevo_usuario}' agregado correctamente")
            self.entry_nuevo_usuario.delete(0, tk.END)
            self.actualizar_lista_usuarios()
        else:
            messagebox.showerror("Error", "No se pudo agregar el usuario")

    def eliminar_usuario(self):
        """Elimina el usuario seleccionado"""
        seleccion = self.lista_usuarios.curselection()
        
        if not seleccion:
            messagebox.showwarning("Selección", "Seleccione un usuario para eliminar")
            return
        
        usuario_a_eliminar = self.lista_usuarios.get(seleccion[0])
        
        if usuario_a_eliminar == self.usuario_actual:
            messagebox.showwarning("Error", "No puede eliminar su propio usuario mientras está conectado")
            return
        
        if messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar al usuario '{usuario_a_eliminar}'?"):
            usuarios_data = cargar_usuarios()
            usuarios = usuarios_data.get("usuarios", [])
            
            if usuario_a_eliminar in usuarios:
                usuarios.remove(usuario_a_eliminar)
                usuarios_data["usuarios"] = usuarios
                
                # También eliminar configuraciones específicas del usuario si existen
                if usuario_a_eliminar in usuarios_data.get("configuraciones", {}):
                    del usuarios_data["configuraciones"][usuario_a_eliminar]
                
                if guardar_usuarios(usuarios_data):
                    messagebox.showinfo("Éxito", f"Usuario '{usuario_a_eliminar}' eliminado correctamente")
                    self.actualizar_lista_usuarios()
                else:
                    messagebox.showerror("Error", "No se pudo eliminar el usuario")
            else:
                messagebox.showwarning("Error", "Usuario no encontrado")

        # ID del registro que se está editando
        self.id_registro_edicion = None

    def crear_interfaz(self):
        """Crea la interfaz con pestañas"""
        # Crear notebook (pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Pestaña 1: Registro
        self.frame_registro = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_registro, text="📝 Nuevo Registro")
        self.crear_formulario_registro()
        
        # Pestaña 2: Ver Registros
        self.frame_ver = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_ver, text="📊 Ver Registros")
        self.crear_vista_registros()

        # Pestaña 3: Configuración
        self.frame_config = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_config, text="⚙️ Configuración")
        self.crear_vista_configuracion()
        
        # Pestaña 4: Gestión de Usuarios
        self.frame_usuarios = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_usuarios, text="👥 Usuarios")
        self.crear_vista_usuarios()

    def crear_formulario_registro(self):
        """Crea el formulario de registro"""
        # Frame principal con scroll
        canvas = tk.Canvas(self.frame_registro, bg="white")
        scrollbar = ttk.Scrollbar(self.frame_registro, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Título
        ttk.Label(scrollable_frame, text="Nuevo Registro de Actividad", 
                 font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Campos del formulario
        row = 1
        
        # Lugar/Dependencia
        ttk.Label(scrollable_frame, text="Lugar/Dependencia:*").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.entry_lugar = ttk.Entry(scrollable_frame, width=50)
        self.entry_lugar.grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        # Solicitante
        ttk.Label(scrollable_frame, text="Solicitante:*").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.entry_solicitante = ttk.Entry(scrollable_frame, width=50)
        self.entry_solicitante.grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        # Tipo de Solicitud (Dropdown)
        ttk.Label(scrollable_frame, text="Tipo de Solicitud:*").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.combo_tipo_solicitud = ttk.Combobox(scrollable_frame, values=self.opciones_tipo_solicitud, width=48)
        self.combo_tipo_solicitud.grid(row=row, column=1, padx=10, pady=5)
        self.combo_tipo_solicitud.current(0)
        row += 1
        
        # Medio de Solicitud (Dropdown)
        ttk.Label(scrollable_frame, text="Medio de Solicitud:*").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.combo_medio = ttk.Combobox(scrollable_frame, values=self.opciones_medio_solicitud, width=48)
        self.combo_medio.grid(row=row, column=1, padx=10, pady=5)
        self.combo_medio.current(0)
        row += 1
        
        # Tipo de Actividad (Dropdown)
        ttk.Label(scrollable_frame, text="Tipo de Actividad:*").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.combo_tipo_actividad = ttk.Combobox(scrollable_frame, values=self.opciones_tipo_actividad, width=48)
        self.combo_tipo_actividad.grid(row=row, column=1, padx=10, pady=5)
        self.combo_tipo_actividad.current(0)
        row += 1
        
        # Descripción
        ttk.Label(scrollable_frame, text="Descripción:*").grid(row=row, column=0, sticky="nw", padx=10, pady=5)
        self.text_descripcion = scrolledtext.ScrolledText(scrollable_frame, width=37, height=5)
        self.text_descripcion.grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        # ¿Cumplida? (Dropdown)
        ttk.Label(scrollable_frame, text="¿Cumplida?:*").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.combo_cumplida = ttk.Combobox(scrollable_frame, values=OPCIONES_CUMPLIDA, width=48)
        self.combo_cumplida.grid(row=row, column=1, padx=10, pady=5)
        self.combo_cumplida.current(1)  # "No" por defecto
        row += 1
        
        # Fecha de Cumplimiento
        ttk.Label(scrollable_frame, text="Fecha de Cumplimiento:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.entry_fecha_cumplimiento = ttk.Entry(scrollable_frame, width=50)
        self.entry_fecha_cumplimiento.grid(row=row, column=1, padx=10, pady=5)
        ttk.Label(scrollable_frame, text="(Formato: YYYY-MM-DD)", 
                 font=("Arial", 8)).grid(row=row+1, column=1, sticky="w", padx=10)
        row += 2
        
        # Observaciones
        ttk.Label(scrollable_frame, text="Observaciones:").grid(row=row, column=0, sticky="nw", padx=10, pady=5)
        self.text_observaciones = scrolledtext.ScrolledText(scrollable_frame, width=37, height=4)
        self.text_observaciones.grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        # Nota de campos requeridos
        ttk.Label(scrollable_frame, text="* Campos requeridos", 
                 font=("Arial", 9, "italic"), foreground="red").grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        
        # Botones
        frame_botones = ttk.Frame(scrollable_frame)
        frame_botones.grid(row=row, column=0, columnspan=2, pady=20)
        
        self.btn_guardar = ttk.Button(frame_botones, text="💾 Guardar Actividad",
                  command=self.guardar_actividad).pack(side="left", padx=5)
        self.btn_limpiar = ttk.Button(frame_botones, text="🔄 Limpiar Formulario",
                  command=self.limpiar_formulario).pack(side="left", padx=5)
        
        # Empaquetar canvas y scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def crear_vista_registros(self):
        """Crea la vista de registros con tabla"""
        # Frame de resumen (dashboard)
        frame_resumen = ttk.LabelFrame(self.frame_ver, text="📊 Resumen de Actividades", padding=10)
        frame_resumen.pack(fill="x", padx=10, pady=5)
        
        # Contadores
        self.label_total_user = ttk.Label(frame_resumen, text="🔴 Total tus actividades: 0")
        self.label_total_user.pack(side="left", padx=15)
        
        self.label_total_all = ttk.Label(frame_resumen, text="🟢 Total general: 0")
        self.label_total_all.pack(side="left", padx=15)
        
        self.label_cumplidas = ttk.Label(frame_resumen, text="✅ Cumplidas: 0")
        self.label_cumplidas.pack(side="left", padx=15)
        
        self.label_pendientes = ttk.Label(frame_resumen, text="⏳ Pendientes: 0")
        self.label_pendientes.pack(side="left", padx=15)
        
        # Frame de búsqueda
        frame_busqueda = ttk.Frame(self.frame_ver)
        frame_busqueda.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame_busqueda, text="🔍 Buscar:").pack(side="left", padx=5)
        self.entry_buscar = ttk.Entry(frame_busqueda, width=30)
        self.entry_buscar.pack(side="left", padx=5)
        ttk.Button(frame_busqueda, text="Buscar", 
                  command=self.buscar).pack(side="left", padx=5)
        
        # Filtro por fecha de cumplimiento
        ttk.Label(frame_busqueda, text="📅 Fecha cumplimiento:").pack(side="left", padx=5)
        self.entry_fecha_filtro = ttk.Entry(frame_busqueda, width=12, 
                                          font=("Arial", 9))
        self.entry_fecha_filtro.pack(side="left", padx=2)
        ttk.Label(frame_busqueda, text="(YYYY-MM-DD)", 
                 font=("Arial", 8)).pack(side="left", padx=2)
        ttk.Button(frame_busqueda, text="Filtrar Fecha", 
                  command=self.filtrar_por_fecha).pack(side="left", padx=5)
        
        ttk.Button(frame_busqueda, text="Mostrar Todos", 
                  command=self.actualizar_tabla).pack(side="left", padx=5)
        
        # Frame de la tabla
        frame_tabla = ttk.Frame(self.frame_ver)
        frame_tabla.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Scrollbars
        scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical")
        scroll_x = ttk.Scrollbar(frame_tabla, orient="horizontal")
        
        # Tabla (Treeview)
        self.tabla = ttk.Treeview(
            frame_tabla,
            columns=COLUMNAS,
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )
        
        scroll_y.config(command=self.tabla.yview)
        scroll_x.config(command=self.tabla.xview)
        
        # Configurar columnas
        for col in COLUMNAS:
            self.tabla.heading(col, text=col)
            if col == "ID":
                self.tabla.column(col, width=50, anchor="center")
            elif col == "USUARIO":
                self.tabla.column(col, width=100, anchor="center")
            elif col == "DESCRIPCIÓN" or col == "OBSERVACIONES":
                self.tabla.column(col, width=200)
            else:
                self.tabla.column(col, width=120)
        
        # Empaquetar tabla y scrollbars
        self.tabla.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        
        # Botones de acción
        frame_acciones = ttk.Frame(self.frame_ver)
        frame_acciones.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(frame_acciones, text="🔄 Actualizar", 
                  command=self.actualizar_tabla).pack(side="left", padx=5)
        ttk.Button(frame_acciones, text="✏️ Editar Seleccionado",
                  command=self.editar_seleccionado).pack(side="left", padx=5)
        ttk.Button(frame_acciones, text="🗑️ Eliminar Seleccionado", 
                  command=self.eliminar_seleccionado).pack(side="left", padx=5)
        ttk.Button(frame_acciones, text="📊 Exportar a Excel", 
                  command=self.exportar_excel).pack(side="left", padx=5)
        
        # Botón de exportación a PDF (deshabilitado si la librería no está disponible)
        self.btn_exportar_pdf = ttk.Button(frame_acciones, text="📄 Exportar a PDF", 
                                          command=self.exportar_pdf, 
                                          state="disabled" if not PDF_AVAILABLE else "normal")
        self.btn_exportar_pdf.pack(side="left", padx=5)
        
        # Info de registros
        self.label_info = ttk.Label(frame_acciones, text="Total: 0 registros")
        self.label_info.pack(side="right", padx=10)
        
        # Bind doble click para ver detalles
        self.tabla.bind("<Double-1>", self.ver_detalles)

    def crear_vista_configuracion(self):
        """Crea la interfaz para la pestaña de configuración."""
        main_frame = ttk.Frame(self.frame_config)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # --- Panel de Dependencias ---
        self.frame_dependencias, self.lista_dependencias = self._crear_panel_config(
            main_frame, "Dependencias", "dependencias", 0
        )

        # --- Panel de Tipos de Actividad ---
        self.frame_actividades, self.lista_actividades = self._crear_panel_config(
            main_frame, "Tipos de Actividad", "tipos_actividad", 1
        )

        # --- Panel de Tipos de Solicitud ---
        self.frame_solicitudes, self.lista_solicitudes = self._crear_panel_config(
            main_frame, "Tipos de Solicitud", "tipos_solicitud", 2
        )

        # --- Panel de Medios de Solicitud ---
        self.frame_medios, self.lista_medios = self._crear_panel_config(
            main_frame, "Medios de Solicitud", "medios_solicitud", 3
        )

    def _crear_panel_config(self, parent, titulo, categoria, grid_row):
        """Helper para crear un panel de configuración reutilizable."""
        frame = ttk.LabelFrame(parent, text=f" 📂 Gestionar {titulo} ", padding=10)
        frame.grid(row=grid_row, column=0, padx=10, pady=10, sticky="ew")
        parent.grid_columnconfigure(0, weight=1)

        # Frame para agregar
        add_frame = ttk.Frame(frame)
        add_frame.pack(fill="x", pady=5)
        entry = ttk.Entry(add_frame, width=40)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        btn_add = ttk.Button(add_frame, text="➕ Agregar",
                             command=lambda c=categoria, e=entry: self.agregar_item(c, e))
        btn_add.pack(side="left")

        ttk.Label(frame, text="(Doble click en un item para editar)", 
                  font=("Arial", 8, "italic")).pack(anchor="w", padx=5, pady=(0, 5))

        # Frame para la lista y eliminación
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill="both", expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        lista_box = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=6)
        scrollbar.config(command=lista_box.yview)
        
        lista_box.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        lista_box.bind("<Double-1>", lambda event, c=categoria, l=lista_box: self.iniciar_edicion_item(event, c, l))

        btn_del = ttk.Button(frame, text="➖ Eliminar Seleccionado",
                             command=lambda c=categoria, l=lista_box: self.eliminar_item(c, l))
        btn_del.pack(pady=5)

        return frame, lista_box

    def crear_vista_usuarios(self):
        """Crea la interfaz para gestionar usuarios"""
        main_frame = ttk.Frame(self.frame_usuarios)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ttk.Label(main_frame, text="👥 Gestión de Usuarios", 
                 font=("Arial", 16, "bold")).pack(pady=10)
        
        # Frame para agregar usuarios
        frame_agregar = ttk.Frame(main_frame)
        frame_agregar.pack(fill="x", pady=10)
        
        ttk.Label(frame_agregar, text="Nuevo usuario:").pack(side="left", padx=5)
        self.entry_nuevo_usuario = ttk.Entry(frame_agregar, width=30)
        self.entry_nuevo_usuario.pack(side="left", padx=5)
        
        btn_agregar = ttk.Button(frame_agregar, text="➕ Agregar", 
                               command=self.agregar_usuario)
        btn_agregar.pack(side="left", padx=5)
        
        # Lista de usuarios
        frame_lista = ttk.Frame(main_frame)
        frame_lista.pack(fill="both", expand=True, pady=10)
        
        scrollbar = ttk.Scrollbar(frame_lista, orient="vertical")
        self.lista_usuarios = tk.Listbox(frame_lista, yscrollcommand=scrollbar.set, height=12)
        scrollbar.config(command=self.lista_usuarios.yview)
        
        self.lista_usuarios.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Botones de acción
        frame_botones = ttk.Frame(main_frame)
        frame_botones.pack(fill="x", pady=10)
        
        btn_eliminar = ttk.Button(frame_botones, text="➖ Eliminar Usuario",
                                command=self.eliminar_usuario)
        btn_eliminar.pack(side="left", padx=5)
        
        btn_actualizar = ttk.Button(frame_botones, text="🔄 Actualizar Lista",
                                 command=self.actualizar_lista_usuarios)
        btn_actualizar.pack(side="left", padx=5)
        
        # Cargar usuarios inicialmente
        self.actualizar_lista_usuarios()

    def cargar_opciones_desde_config(self):
        """Carga las listas de opciones desde el archivo de configuración."""
        config = cargar_config()
        self.opciones_tipo_solicitud = config.get("tipos_solicitud", DEFAULTS["tipos_solicitud"])
        self.opciones_medio_solicitud = config.get("medios_solicitud", DEFAULTS["medios_solicitud"])
        self.opciones_tipo_actividad = config.get("tipos_actividad", DEFAULTS["tipos_actividad"])
        self.opciones_dependencias = config.get("dependencias", DEFAULTS["dependencias"])

    def actualizar_componentes_config(self):
        """Recarga las opciones y actualiza todos los componentes de la UI."""
        self.cargar_opciones_desde_config()
        
        # Actualizar comboboxes en el formulario de registro
        self.combo_tipo_solicitud['values'] = self.opciones_tipo_solicitud
        self.combo_medio['values'] = self.opciones_medio_solicitud
        self.combo_tipo_actividad['values'] = self.opciones_tipo_actividad
        
        # Actualizar listas en la pestaña de configuración
        self.actualizar_listas_config()

    def actualizar_listas_config(self):
        """Refresca el contenido de las Listbox en la pestaña de configuración."""
        listas_map = {
            "dependencias": (self.lista_dependencias, self.opciones_dependencias),
            "tipos_actividad": (self.lista_actividades, self.opciones_tipo_actividad),
            "tipos_solicitud": (self.lista_solicitudes, self.opciones_tipo_solicitud),
            "medios_solicitud": (self.lista_medios, self.opciones_medio_solicitud),
        }
        for categoria, (lista_box, opciones) in listas_map.items():
            lista_box.delete(0, tk.END)
            for item in opciones:
                lista_box.insert(tk.END, item)

    def validar_campos(self):
        """Valida que los campos requeridos estén llenos"""
        if not self.entry_lugar.get().strip():
            messagebox.showwarning("Validación", "El campo 'Lugar/Dependencia' es requerido")
            return False
        
        if not self.entry_solicitante.get().strip():
            messagebox.showwarning("Validación", "El campo 'Solicitante' es requerido")
            return False
        
        if not self.combo_tipo_solicitud.get().strip():
            messagebox.showwarning("Validación", "El campo 'Tipo de Solicitud' es requerido")
            return False
        
        if not self.combo_medio.get().strip():
            messagebox.showwarning("Validación", "El campo 'Medio de Solicitud' es requerido")
            return False
        
        if not self.combo_tipo_actividad.get().strip():
            messagebox.showwarning("Validación", "El campo 'Tipo de Actividad' es requerido")
            return False
        
        if not self.text_descripcion.get("1.0", "end").strip():
            messagebox.showwarning("Validación", "El campo 'Descripción' es requerido")
            return False
        
        return True

    def guardar_actividad(self):
        """Guarda una nueva actividad o actualiza una existente"""
        if not self.validar_campos():
            return
        
        data = {
            "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "USUARIO": self.usuario_actual,
            "DEPENDENCIA": self.entry_lugar.get().strip(),
            "SOLICITANTE": self.entry_solicitante.get().strip(),
            "TIPO DE SOLICITUD": self.combo_tipo_solicitud.get(),
            "MEDIO DE SOLICITUD": self.combo_medio.get(),
            "TIPO DE ACTIVIDAD": self.combo_tipo_actividad.get(),
            "DESCRIPCIÓN": self.text_descripcion.get("1.0", "end").strip(),
            "CUMPLIDO": self.combo_cumplida.get(),
            "FECHA ATENCIÓN": self.entry_fecha_cumplimiento.get().strip(),
            "OBSERVACIONES": self.text_observaciones.get("1.0", "end").strip(),
        }

        if self.id_registro_edicion:
            # Actualizar registro existente
            if actualizar_registro(self.id_registro_edicion, data, self.usuario_actual):
                messagebox.showinfo("✅ Actualizado", f"Actividad ID {self.id_registro_edicion} actualizada exitosamente.")
                self.limpiar_formulario() # También resetea el modo edición
                self.actualizar_tabla()
                self.notebook.select(self.frame_ver) # Volver a la pestaña de registros
        else:
            # Guardar nuevo registro
            nuevo_id = guardar_registro(data)
            if nuevo_id:
                messagebox.showinfo("✅ Guardado", f"Actividad registrada exitosamente con ID: {nuevo_id}")
                self.limpiar_formulario()
                self.actualizar_tabla()

    def limpiar_formulario(self):
        """Limpia todos los campos del formulario"""
        self.entry_lugar.delete(0, tk.END)
        self.entry_solicitante.delete(0, tk.END)
        self.combo_tipo_solicitud.current(0)
        self.combo_medio.current(0)
        self.combo_tipo_actividad.current(0)
        self.text_descripcion.delete("1.0", tk.END)
        self.combo_cumplida.current(1)
        self.entry_fecha_cumplimiento.delete(0, tk.END)
        self.text_observaciones.delete("1.0", tk.END)

        # Resetear modo edición
        self.id_registro_edicion = None
        self.btn_guardar.config(text="💾 Guardar Actividad")
        self.root.title("📋 Gestor de Actividades - Versión Pro")

    def agregar_item(self, categoria, entry_widget):
        """Manejador para el botón de agregar en la configuración."""
        nuevo_item = entry_widget.get().strip()
        if not nuevo_item:
            messagebox.showwarning("Entrada Vacía", "El campo no puede estar vacío.")
            return
        
        if agregar_item_config(categoria, nuevo_item):
            messagebox.showinfo("Éxito", f"'{nuevo_item}' agregado a la categoría '{categoria}'.")
            entry_widget.delete(0, tk.END)
            self.actualizar_componentes_config()
        else:
            messagebox.showwarning("Duplicado", f"'{nuevo_item}' ya existe en esta categoría.")

    def eliminar_item(self, categoria, listbox_widget):
        """Manejador para el botón de eliminar en la configuración."""
        seleccion = listbox_widget.curselection()
        if not seleccion:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un item de la lista para eliminar.")
            return
        
        item_a_eliminar = listbox_widget.get(seleccion[0])
        
        if messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar '{item_a_eliminar}'?"):
            if eliminar_item_config(categoria, item_a_eliminar):
                messagebox.showinfo("Éxito", f"'{item_a_eliminar}' ha sido eliminado.")
                self.actualizar_componentes_config()

    def iniciar_edicion_item(self, event, categoria, listbox_widget):
        """Abre un diálogo para editar un item seleccionado de una lista de configuración."""
        seleccion = listbox_widget.curselection()
        if not seleccion:
            return

        valor_original = listbox_widget.get(seleccion[0])

        # Crear diálogo
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar Item")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=f"Editando en '{categoria.replace('_', ' ').title()}':").pack(pady=10)

        entry_nuevo_valor = ttk.Entry(dialog, width=50)
        entry_nuevo_valor.pack(pady=5, padx=20)
        entry_nuevo_valor.insert(0, valor_original)
        entry_nuevo_valor.focus_set()
        entry_nuevo_valor.selection_range(0, tk.END)

        def guardar_cambios():
            nuevo_valor = entry_nuevo_valor.get().strip()
            if not nuevo_valor:
                messagebox.showwarning("Entrada Vacía", "El valor no puede estar vacío.", parent=dialog)
                return
            if nuevo_valor.upper() == valor_original.upper():
                dialog.destroy()
                return

            if actualizar_item_config(categoria, valor_original, nuevo_valor):
                self.actualizar_componentes_config()
                dialog.destroy()
            else:
                messagebox.showerror("Error", "No se pudo actualizar el item.\nEs posible que el nuevo nombre ya exista.", parent=dialog)

        frame_botones = ttk.Frame(dialog)
        frame_botones.pack(pady=10)
        ttk.Button(frame_botones, text="Guardar", command=guardar_cambios).pack(side="left", padx=10)
        ttk.Button(frame_botones, text="Cancelar", command=dialog.destroy).pack(side="left", padx=10)
        dialog.bind("<Return>", lambda event: guardar_cambios())
        dialog.bind("<Escape>", lambda event: dialog.destroy())
        dialog.wait_window()

    def actualizar_tabla(self):
        """Actualiza la tabla con los registros del usuario"""
        # Limpiar tabla
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        
        # Cargar registros (filtrados por usuario si no es admin)
        df = cargar_registros(self.usuario_actual)
        
        # Insertar registros en la tabla
        for _, row in df.iterrows():
            valores = [row[col] for col in COLUMNAS]
            self.tabla.insert("", "end", values=valores)
        
        # Actualizar contadores
        self.actualizar_contadores(df)
        # Actualizar contador
        self.label_info.config(text=f"Total: {len(df)} registros")
    
    def actualizar_contadores(self, df_actual=None):
        """Actualiza los contadores de actividades"""
        # Cargar todos los registros para estadísticas generales
        df_all = cargar_registros()  # Sin usuario para obtener todos los registros
        df_user = cargar_registros(self.usuario_actual)  # Solo registros del usuario
        
        # Calcular totales
        total_general = len(df_all)
        total_user = len(df_user)
        
        # Calcular actividades cumplidas y pendientes
        cumplidas = len(df_user[df_user["CUMPLIDO"] == "Sí"])
        pendientes = total_user - cumplidas
        
        # Actualizar etiquetas
        self.label_total_user.config(text=f"🔴 Total tus actividades: {total_user}")
        self.label_total_all.config(text=f"🟢 Total general: {total_general}")
        self.label_cumplidas.config(text=f"✅ Cumplidas: {cumplidas}")
        self.label_pendientes.config(text=f"⏳ Pendientes: {pendientes}")

    def buscar(self):
        """Busca registros por término"""
        termino = self.entry_buscar.get().strip()
        
        if not termino:
            messagebox.showwarning("Búsqueda", "Ingrese un término de búsqueda")
            return
        
        # Limpiar tabla
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        
        # Buscar registros (filtrados por usuario si no es admin)
        df = buscar_registros(termino, self.usuario_actual)
        
        # Insertar resultados
        for _, row in df.iterrows():
            valores = [row[col] for col in COLUMNAS]
            self.tabla.insert("", "end", values=valores)
        
        # Actualizar contadores y etiqueta
        self.actualizar_contadores(df)
        self.label_info.config(text=f"Resultados: {len(df)} registros")
        
        if df.empty:
            messagebox.showinfo("Búsqueda", f"No se encontraron registros con '{termino}'")

    def filtrar_por_fecha(self):
        """Filtra registros por fecha de cumplimiento"""
        fecha_filtro = self.entry_fecha_filtro.get().strip()
        
        if not fecha_filtro:
            messagebox.showwarning("Filtro", "Ingrese una fecha para filtrar (YYYY-MM-DD)")
            return
        
        # Validar formato de fecha
        try:
            datetime.strptime(fecha_filtro, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Formato", "Formato de fecha inválido. Use YYYY-MM-DD")
            return
        
        # Limpiar tabla
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        
        # Cargar y filtrar registros (filtrados por usuario si no es admin)
        df = cargar_registros(self.usuario_actual)
        
        if df.empty:
            messagebox.showinfo("Filtro", "No hay registros para filtrar")
            return
        
        # Filtrar por fecha de cumplimiento (insensible a mayúsculas/minúsculas)
        # Convertir ambas fechas a string para comparación
        df_filtrado = df[df["FECHA ATENCIÓN"].astype(str).str.contains(fecha_filtro, na=False)]
        
        # Insertar resultados filtrados
        for _, row in df_filtrado.iterrows():
            valores = [row[col] for col in COLUMNAS]
            self.tabla.insert("", "end", values=valores)
        
        # Actualizar contadores y etiqueta
        self.actualizar_contadores(df_filtrado)
        self.label_info.config(text=f"Filtrados: {len(df_filtrado)} de {len(df)} registros")
        
        if df_filtrado.empty:
            messagebox.showinfo("Filtro", f"No se encontraron registros con fecha '{fecha_filtro}'")

    def editar_seleccionado(self):
        """Carga los datos de un registro en el formulario para su edición"""
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Editar", "Seleccione un registro para editar")
            return

        # Obtener datos del registro
        item = self.tabla.item(seleccion[0])
        valores = item['values']
        datos_registro = {col: val for col, val in zip(COLUMNAS, valores)}

        # Limpiar formulario antes de llenarlo
        self.limpiar_formulario()

        # Llenar el formulario con los datos
        self.id_registro_edicion = datos_registro["ID"]
        self.entry_lugar.insert(0, datos_registro.get("DEPENDENCIA", ""))
        self.entry_solicitante.insert(0, datos_registro.get("SOLICITANTE", ""))
        self.combo_tipo_solicitud.set(datos_registro.get("TIPO DE SOLICITUD", ""))
        self.combo_medio.set(datos_registro.get("MEDIO DE SOLICITUD", ""))
        self.combo_tipo_actividad.set(datos_registro.get("TIPO DE ACTIVIDAD", ""))
        self.text_descripcion.insert("1.0", datos_registro.get("DESCRIPCIÓN", ""))
        self.combo_cumplida.set(datos_registro.get("CUMPLIDO", "No"))
        self.entry_fecha_cumplimiento.insert(0, str(datos_registro.get("FECHA ATENCIÓN", "")))
        self.text_observaciones.insert("1.0", datos_registro.get("OBSERVACIONES", ""))

        # Cambiar a modo edición
        self.btn_guardar.config(text="💾 Actualizar Actividad")
        self.root.title(f"✏️ Editando Registro ID: {self.id_registro_edicion}")
        
        # Cambiar a la pestaña de registro
        self.notebook.select(self.frame_registro)
        self.entry_lugar.focus_set()

    def eliminar_seleccionado(self):
        """Elimina el registro seleccionado"""
        seleccion = self.tabla.selection()
        
        if not seleccion:
            messagebox.showwarning("Eliminar", "Seleccione un registro para eliminar")
            return
        
        # Obtener ID del registro seleccionado
        item = self.tabla.item(seleccion[0])
        id_registro = item['values'][0]
        
        # Confirmar eliminación
        respuesta = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro de eliminar el registro ID {id_registro}?"
        )
        
        if respuesta:
            if eliminar_registro(id_registro, self.usuario_actual):
                messagebox.showinfo("✅ Eliminado", "Registro eliminado exitosamente")
                self.actualizar_tabla()

    def ver_detalles(self, event):
        """Muestra los detalles de un registro al hacer doble click"""
        seleccion = self.tabla.selection()
        
        if not seleccion:
            return
        
        item = self.tabla.item(seleccion[0])
        valores = item['values']
        
        # Crear ventana de detalles
        ventana = tk.Toplevel(self.root)
        ventana.title(f"Detalles - ID {valores[0]}")
        ventana.geometry("500x600")
        
        # Mostrar detalles
        texto = scrolledtext.ScrolledText(ventana, wrap=tk.WORD, width=60, height=30)
        texto.pack(padx=10, pady=10, fill="both", expand=True)
        
        for i, col in enumerate(COLUMNAS):
            texto.insert(tk.END, f"{col}:\n", "bold")
            texto.insert(tk.END, f"{valores[i]}\n\n")
        
        texto.tag_config("bold", font=("Arial", 10, "bold"))
        texto.config(state="disabled")
        
        ttk.Button(ventana, text="Cerrar", command=ventana.destroy).pack(pady=10)

    def exportar_excel(self):
        """Exporta los registros actuales a un nuevo Excel"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_export = f"actividades_export_{timestamp}.xlsx"
            
            df = cargar_registros(self.usuario_actual)
            df.to_excel(nombre_export, index=False)
            
            messagebox.showinfo(
                "✅ Exportado",
                f"Datos exportados exitosamente a:\n{nombre_export}"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")

    def exportar_pdf(self):
        """Exporta los registros actuales a un archivo PDF"""
        if not PDF_AVAILABLE:
            messagebox.showerror("Error", "La funcionalidad de exportación a PDF no está disponible.\n\nInstale la librería FPDF con: pip install fpdf")
            return
        
        try:
            # Obtener datos actuales (filtrados por usuario si no es admin)
            df = cargar_registros(self.usuario_actual)
            
            if df.empty:
                messagebox.showwarning("Exportar", "No hay registros para exportar")
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"actividades_export_{timestamp}.pdf"
            
            # Crear PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            # Título
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Reporte de Actividades", 0, 1, "C")
            pdf.ln(5)
            
            # Información del reporte
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 8, f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
            pdf.cell(0, 8, f"Usuario: {self.usuario_actual}", 0, 1)
            pdf.cell(0, 8, f"Total de registros: {len(df)}", 0, 1)
            pdf.ln(10)
            
            # Configurar tabla
            pdf.set_font("Arial", "B", 8)
            
            # Anchos de columna (ajustados para PDF, incluyendo USUARIO)
            column_widths = [10, 15, 25, 20, 25, 25, 25, 25, 40, 15, 20, 30]
            
            # Encabezados de tabla
            for i, col in enumerate(COLUMNAS):
                if i < len(column_widths):
                    pdf.cell(column_widths[i], 8, str(col)[:20], 1, 0, "C")
            pdf.ln()
            
            # Datos de la tabla
            pdf.set_font("Arial", "", 7)
            
            for _, row in df.iterrows():
                for i, col in enumerate(COLUMNAS):
                    if i < len(column_widths):
                        valor = str(row[col]) if pd.notna(row[col]) else ""
                        # Truncar texto largo para que quepa en la celda
                        if len(valor) > 30:
                            valor = valor[:27] + "..."
                        pdf.cell(column_widths[i], 6, valor, 1, 0, "L")
                pdf.ln()
            
            # Guardar PDF
            pdf.output(nombre_archivo)
            
            messagebox.showinfo(
                "✅ Exportado a PDF",
                f"Reporte exportado exitosamente a:\n{nombre_archivo}"
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar a PDF: {str(e)}")

# ==================== MAIN ====================

def main():
    """Función principal que maneja el flujo de login y aplicación"""
    # Inicializar archivos si no existen
    inicializar_usuarios()
    inicializar_config()
    inicializar_excel()
    
    # Crear ventana principal (inicialmente oculta)
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana principal hasta el login
    
    # Variable para almacenar el usuario seleccionado
    usuario_seleccionado = [None]
    
    def on_login_success(usuario):
        """Callback llamado cuando el usuario se loguea exitosamente"""
        usuario_seleccionado[0] = usuario
        root.deiconify()  # Mostrar ventana principal
        app = AplicacionActividades(root, usuario)
        
    # Mostrar ventana de login
    mostrar_login(root, on_login_success)
    
    # Iniciar el bucle principal
    root.mainloop()

if __name__ == "__main__":
    main()
