"""
Módulo: main_gui.py (Versión Definitiva e Integral)
Proyecto: SICAV-Café - Cafetería y Repostería Artesanal "Cielito Lindo"
Autor: Mario Gustavo Trujillo Chua
Descripción: Interfaz gráfica de escritorio intuitiva y moderna para PC con
             todas las funciones del sistema, roles RBAC y generadores PDF.
"""

import os
import subprocess
import platform
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime

from models_and_controllers import (
    GestorBaseDeDatos,
    Usuario,
    Producto,
    Insumo,
    DetalleVenta,
    Venta,
    Merma,
    CorteCaja,
    Reporte
)


class AplicacionSICAVCafe(tk.Tk):
    """Ventana principal integral e intuitiva para SICAV-Café."""

    def __init__(self):
        super().__init__()
        self.title("SICAV-Café | Cafetería 'Cielito Lindo'")
        self.geometry("1240x720")
        self.minsize(1024, 620)
        self.configure(bg="#F1F5F9")

        GestorBaseDeDatos.inicializar_bd()

        self.usuario_actual = Usuario()
        self.venta_activa = Venta()

        self._configurar_estilos()
        self.mostrar_pantalla_login()

    def _configurar_estilos(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#F1F5F9")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#E2E8F0", foreground="#1E293B")
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=28)

    def _limpiar_ventana(self):
        for widget in self.winfo_children():
            widget.destroy()

    @staticmethod
    def _abrir_archivo_pdf(ruta: str):
        if not os.path.exists(ruta):
            messagebox.showwarning("Archivo no encontrado", f"No se encontró el archivo:\n{ruta}")
            return
        try:
            if platform.system() == "Windows":
                os.startfile(ruta)  # type: ignore
            elif platform.system() == "Darwin":
                subprocess.call(["open", ruta])
            else:
                subprocess.call(["xdg-open", ruta])
        except Exception as e:
            messagebox.showinfo("Documento PDF", f"Guardado en:\n{ruta}\n({e})")

    # ========================================================================
    # PANTALLA DE LOGIN
    # ========================================================================
    def mostrar_pantalla_login(self):
        self._limpiar_ventana()

        card = tk.Frame(self, bg="#FFFFFF", bd=1, relief="solid", padx=45, pady=40)
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(card, text="☕", bg="#FFFFFF", font=("Segoe UI", 32)).pack(pady=(0, 5))
        tk.Label(card, text="SICAV-Café", bg="#FFFFFF", fg="#0F172A", font=("Segoe UI", 20, "bold")).pack()
        tk.Label(card, text="Cafetería y Repostería Artesanal 'Cielito Lindo'", bg="#FFFFFF", fg="#64748B", font=("Segoe UI", 10)).pack(pady=(2, 25))

        tk.Label(card, text="Usuario de Acceso:", bg="#FFFFFF", fg="#334155", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.ent_usuario = ttk.Entry(card, width=32, font=("Segoe UI", 11))
        self.ent_usuario.pack(pady=(4, 15))
        self.ent_usuario.insert(0, "admin_roberto")

        tk.Label(card, text="Contraseña:", bg="#FFFFFF", fg="#334155", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.ent_password = ttk.Entry(card, width=32, font=("Segoe UI", 11), show="*")
        self.ent_password.pack(pady=(4, 20))
        self.ent_password.insert(0, "admin123")

        btn_entrar = tk.Button(
            card, text="Ingresar al Sistema", bg="#0284C7", fg="#FFFFFF",
            font=("Segoe UI", 11, "bold"), relief="flat", pady=10,
            command=self._evento_login
        )
        btn_entrar.pack(fill="x")

        tk.Label(
            card, text="💡 Admin: admin_roberto / admin123\n💡 Cajero: cajera_mariana / cajero123",
            bg="#F8FAFC", fg="#475569", font=("Consolas", 9), justify="left", padx=12, pady=10
        ).pack(fill="x", pady=(20, 0))

        self.ent_usuario.focus_set()
        self.bind("<Return>", lambda _: self._evento_login())

    def _evento_login(self):
        try:
            if self.usuario_actual.iniciarSesion(self.ent_usuario.get(), self.ent_password.get()):
                self.unbind("<Return>")
                self.venta_activa.crearVenta(self.usuario_actual.idUsuario)
                self.mostrar_panel_principal()
            else:
                messagebox.showerror("Acceso Denegado", "Usuario, contraseña incorrectos o cuenta inactiva.")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    # ========================================================================
    # PANEL PRINCIPAL (MENÚ LATERAL + ÁREA DE TRABAJO)
    # ========================================================================
    def mostrar_panel_principal(self):
        self._limpiar_ventana()

        topbar = tk.Frame(self, bg="#0F172A", height=50, padx=20)
        topbar.pack(side="top", fill="x")

        tk.Label(topbar, text="☕ SICAV-Café | Sistema Integral", bg="#0F172A", fg="#38BDF8", font=("Segoe UI", 11, "bold")).pack(side="left")
        tk.Label(topbar, text=f"Operador: {self.usuario_actual.nombreCompleto} ({self.usuario_actual.rol})", bg="#0F172A", fg="#F8FAFC", font=("Segoe UI", 10)).pack(side="right")

        main_container = tk.Frame(self, bg="#F1F5F9")
        main_container.pack(side="top", fill="both", expand=True)

        self.sidebar = tk.Frame(main_container, bg="#1E293B", width=220, padx=10, pady=15)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.content_area = tk.Frame(main_container, bg="#F1F5F9", padx=15, pady=15)
        self.content_area.pack(side="right", fill="both", expand=True)

        # Botones de navegación comunes
        self._crear_boton_menu("🛒 Punto de Venta", lambda: self.cambiar_vista("pos"))
        self._crear_boton_menu("📦 Inventario y Mermas", lambda: self.cambiar_vista("stock"))
        self._crear_boton_menu("💰 Arqueo de Caja", lambda: self.cambiar_vista("corte"))
        self._crear_boton_menu("📄 Historial y Visor PDF", lambda: self.cambiar_vista("historial"))

        # Opciones exclusivas de Administrador (RBAC)
        if self.usuario_actual.rol == "Administrador":
            tk.Label(self.sidebar, text="--- ADMIN ---", bg="#1E293B", fg="#94A3B8", font=("Segoe UI", 9, "bold")).pack(pady=(15, 5))
            self._crear_boton_menu("⚙️ Catálogo y Recetas", lambda: self.cambiar_vista("catalogo"))
            self._crear_boton_menu("📊 Reportes PDF", lambda: self.cambiar_vista("reportes"))
            self._crear_boton_menu("👥 Gestión Usuarios", lambda: self.cambiar_vista("usuarios"))
            self._crear_boton_menu("💾 Respaldar Base Datos", self._evento_respaldar_bd, color="#10B981")

        tk.Button(
            self.sidebar, text="🔒 Cerrar Sesión", bg="#EF4444", fg="#FFFFFF",
            font=("Segoe UI", 10, "bold"), relief="flat", pady=8,
            command=self._evento_cerrar_sesion
        ).pack(side="bottom", fill="x", pady=10)

        self.cambiar_vista("pos")

    def _crear_boton_menu(self, texto, comando, color="#334155"):
        btn = tk.Button(
            self.sidebar, text=texto, bg=color, fg="#FFFFFF", anchor="w",
            font=("Segoe UI", 10), relief="flat", padx=10, pady=8, command=comando
        )
        btn.pack(fill="x", pady=4)

    def limpiar_area_contenido(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()

    def cambiar_vista(self, vista):
        self.limpiar_area_contenido()
        if vista == "pos":
            self.vista_punto_de_venta()
        elif vista == "stock":
            self.vista_inventario()
        elif vista == "corte":
            self.vista_corte_caja()
        elif vista == "historial":
            self.vista_historial()
        elif vista == "catalogo" and self.usuario_actual.rol == "Administrador":
            self.vista_catalogo()
        elif vista == "reportes" and self.usuario_actual.rol == "Administrador":
            self.vista_reportes()
        elif vista == "usuarios" and self.usuario_actual.rol == "Administrador":
            self.vista_usuarios()

    def _evento_cerrar_sesion(self):
        self.usuario_actual.cerrarSesion()
        self.mostrar_pantalla_login()

    def _evento_respaldar_bd(self):
        ruta = filedialog.asksaveasfilename(
            title="Respaldar Base de Datos", defaultextension=".db",
            initialfile=f"Respaldo_SICAV_{datetime.now().strftime('%Y%m%d')}.db",
            filetypes=[("SQLite DB", "*.db")]
        )
        if ruta:
            GestorBaseDeDatos.respaldar_base_de_datos(ruta)
            messagebox.showinfo("Respaldo", f"Base de datos guardada en:\n{ruta}")

    # ========================================================================
    # VISTA 1: PUNTO DE VENTA (RF-02, RF-03, RF-04, RF-05)
    # ========================================================================
    def vista_punto_de_venta(self):
        left_frame = tk.Frame(self.content_area, bg="#F1F5F9")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right_frame = tk.Frame(self.content_area, bg="#FFFFFF", bd=1, relief="solid", padx=15, pady=15)
        right_frame.pack(side="right", fill="both", expand=True)

        tk.Label(left_frame, text="Catálogo de Productos", bg="#F1F5F9", fg="#0F172A", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 8))

        cols = ("id", "nombre", "categoria", "precio")
        self.tree_productos = ttk.Treeview(left_frame, columns=cols, show="headings", height=12)
        for c, t, w in [("id", "ID", 40), ("nombre", "Producto", 180), ("categoria", "Categoría", 110), ("precio", "Precio", 80)]:
            self.tree_productos.heading(c, text=t)
            self.tree_productos.column(c, width=w, anchor="center" if c != "nombre" else "w")
        self.tree_productos.pack(fill="both", expand=True, pady=(0, 10))

        frm_add = tk.Frame(left_frame, bg="#FFFFFF", bd=1, relief="solid", padx=10, pady=10)
        frm_add.pack(fill="x")

        tk.Label(frm_add, text="Cantidad:", bg="#FFFFFF", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", padx=5)
        self.ent_cant = ttk.Entry(frm_add, width=8, font=("Segoe UI", 10))
        self.ent_cant.grid(row=0, column=1, sticky="w", padx=5)
        self.ent_cant.insert(0, "1")

        tk.Label(frm_add, text="Modificador (Extra):", bg="#FFFFFF", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.cmb_mod = ttk.Combobox(
            frm_add, state="readonly", width=28,
            values=["Sin modificador", "Leche de Almendra (+$12)", "Shot Extra Espresso (+$15)", "Jarabe Extra Vainilla (+$10)"]
        )
        self.cmb_mod.current(0)
        self.cmb_mod.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        tk.Button(
            frm_add, text="➕ Agregar a la Venta", bg="#0284C7", fg="#FFFFFF",
            font=("Segoe UI", 10, "bold"), relief="flat", pady=6, command=self._pos_agregar
        ).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        tk.Label(right_frame, text="Comanda en Curso", bg="#FFFFFF", fg="#0F172A", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 8))

        cols_cmd = ("cant", "desc", "sub")
        self.tree_cmd = ttk.Treeview(right_frame, columns=cols_cmd, show="headings", height=8)
        for c, t, w in [("cant", "Cant", 50), ("desc", "Descripción", 180), ("sub", "Subtotal", 80)]:
            self.tree_cmd.heading(c, text=t)
            self.tree_cmd.column(c, width=w, anchor="center" if c != "desc" else "w")
        self.tree_cmd.pack(fill="x", pady=(0, 5))

        tk.Button(right_frame, text="🗑️ Vaciar Comanda", bg="#94A3B8", fg="#FFFFFF", font=("Segoe UI", 9), relief="flat", command=self._pos_limpiar).pack(anchor="e", pady=(0, 10))

        self.lbl_sub = tk.Label(right_frame, text="Subtotal: $0.00", bg="#FFFFFF", font=("Segoe UI", 10), anchor="w")
        self.lbl_sub.pack(fill="x")
        self.lbl_iv = tk.Label(right_frame, text="IVA (16%): $0.00", bg="#FFFFFF", font=("Segoe UI", 10), anchor="w")
        self.lbl_iv.pack(fill="x")
        self.lbl_tot = tk.Label(right_frame, text="TOTAL: $0.00", bg="#FFFFFF", fg="#0284C7", font=("Segoe UI", 14, "bold"), anchor="w")
        self.lbl_tot.pack(fill="x", pady=(5, 10))

        tk.Label(right_frame, text="Método de Pago:", bg="#FFFFFF", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.cmb_pago = ttk.Combobox(right_frame, state="readonly", values=["Efectivo", "Tarjeta", "Transferencia"], width=25)
        self.cmb_pago.current(0)
        self.cmb_pago.pack(fill="x", pady=(2, 8))

        tk.Label(right_frame, text="Efectivo Recibido ($):", bg="#FFFFFF", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.ent_recibido = ttk.Entry(right_frame, font=("Segoe UI", 11))
        self.ent_recibido.pack(fill="x", pady=(2, 12))

        tk.Button(
            right_frame, text="✅ COBRAR E IMPRIMIR PDF", bg="#10B981", fg="#FFFFFF",
            font=("Segoe UI", 11, "bold"), relief="flat", pady=10, command=self._pos_cobrar
        ).pack(fill="x")

        self._cargar_productos_pos()

    def _cargar_productos_pos(self):
        for r in self.tree_productos.get_children():
            self.tree_productos.delete(r)
        conn = GestorBaseDeDatos.obtener_conexion()
        prods = conn.execute("SELECT * FROM productos WHERE disponible = 1").fetchall()
        conn.close()
        for p in prods:
            self.tree_productos.insert("", "end", values=(p["id_producto"], p["nombre_producto"], p["categoria"], f"{p['precio']:.2f}"))

    def _pos_agregar(self):
        sel = self.tree_productos.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un producto del catálogo.")
            return
        v = self.tree_productos.item(sel[0], "values")
        id_p, nom, precio = int(v[0]), str(v[1]), float(v[3])

        mod_idx = self.cmb_mod.current()
        extra, desc_m, ins_id, cant_ex = 0.0, "", None, 0.0
        if mod_idx == 1:
            extra, desc_m, ins_id, cant_ex = 12.00, "+Leche Almendra", 3, 0.220
        elif mod_idx == 2:
            extra, desc_m, ins_id, cant_ex = 15.00, "+Shot Espresso", 1, 0.018
        elif mod_idx == 3:
            extra, desc_m, ins_id, cant_ex = 10.00, "+Jarabe Vainilla", 5, 0.030

        try:
            det = DetalleVenta(len(self.venta_activa.detalles) + 1, 0, id_p, nom, self.ent_cant.get(), precio + extra, desc_m, ins_id, cant_ex)
            self.venta_activa.agregarDetalle(det)
            self._refrescar_comanda_gui()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _refrescar_comanda_gui(self):
        for r in self.tree_cmd.get_children():
            self.tree_cmd.delete(r)
        for d in self.venta_activa.detalles:
            self.tree_cmd.insert("", "end", values=(d.cantidad, f"{d.nombreProducto} {d.descripcionModificador}", f"${d.subtotal:.2f}"))
        self.lbl_sub.config(text=f"Subtotal: ${self.venta_activa.subtotal:.2f}")
        self.lbl_iv.config(text=f"IVA (16%): ${self.venta_activa.iva:.2f}")
        self.lbl_tot.config(text=f"TOTAL: ${self.venta_activa.total:.2f}")

    def _pos_limpiar(self):
        self.venta_activa.crearVenta(self.usuario_actual.idUsuario)
        self._refrescar_comanda_gui()
        self.ent_recibido.delete(0, "end")

    def _pos_cobrar(self):
        try:
            metodo = self.cmb_pago.get()
            monto = self.ent_recibido.get() if metodo == "Efectivo" else str(self.venta_activa.total)
            if self.venta_activa.procesarPago(monto, metodo):
                pdf = self.venta_activa.rutaUltimoPDF
                messagebox.showinfo("Éxito", f"Venta #{self.venta_activa.idVenta:05d} cobrada.\nCambio: ${self.venta_activa.cambio:.2f}")
                self._abrir_archivo_pdf(pdf)
                self._pos_limpiar()
        except ValueError as e:
            messagebox.showerror("Error en Cobro", str(e))

    # ========================================================================
    # VISTA 2: INVENTARIO, SEMÁFORO, MERMAS Y ABASTECIMIENTO (RF-08, RF-09, RF-10)
    # ========================================================================
    def vista_inventario(self):
        tk.Label(self.content_area, text="Control de Inventario y Semáforo de Stock", bg="#F1F5F9", fg="#0F172A", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 10))

        cols = ("id", "insumo", "actual", "min", "unidad", "costo", "semaforo")
        self.tree_ins = ttk.Treeview(self.content_area, columns=cols, show="headings", height=9)
        for c, t, w in [("id", "ID", 40), ("insumo", "Insumo", 220), ("actual", "Actual", 90), ("min", "Mínimo", 90), ("unidad", "Unidad", 80), ("costo", "Costo", 90), ("semaforo", "Estado", 180)]:
            self.tree_ins.heading(c, text=t)
            self.tree_ins.column(c, width=w, anchor="center" if c != "insumo" else "w")

        self.tree_ins.tag_configure("VERDE", background="#DCFCE7", foreground="#166534")
        self.tree_ins.tag_configure("AMARILLO", background="#FEF9C3", foreground="#854D0E")
        self.tree_ins.tag_configure("ROJO", background="#FEE2E2", foreground="#991B1B")
        self.tree_ins.pack(fill="x", pady=(0, 15))

        # Panel inferior dividido: Izquierda (Merma), Derecha (Abastecimiento)
        frm_inferior = tk.Frame(self.content_area, bg="#F1F5F9")
        frm_inferior.pack(fill="x", expand=True)

        # Formulario de Merma (RF-10)
        frm_m = tk.Frame(frm_inferior, bg="#FFFFFF", bd=1, relief="solid", padx=15, pady=12)
        frm_m.pack(side="left", fill="both", expand=True, padx=(0, 8))
        tk.Label(frm_m, text="Registrar Pérdida o Merma", bg="#FFFFFF", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))

        tk.Label(frm_m, text="Cantidad:", bg="#FFFFFF").pack(anchor="w")
        self.ent_m_cant = ttk.Entry(frm_m, width=15)
        self.ent_m_cant.pack(anchor="w", pady=(2, 6))

        tk.Label(frm_m, text="Motivo:", bg="#FFFFFF").pack(anchor="w")
        self.cmb_m_motivo = ttk.Combobox(frm_m, values=["Calibración de molino", "Derrame accidental", "Caducidad"], width=22, state="readonly")
        self.cmb_m_motivo.current(0)
        self.cmb_m_motivo.pack(anchor="w", pady=(2, 8))

        tk.Button(frm_m, text="⚠️ Registrar Merma", bg="#F59E0B", fg="#FFFFFF", font=("Segoe UI", 9, "bold"), relief="flat", padx=10, command=self._evento_merma).pack(anchor="w")

        # Formulario de Abastecimiento (RF-09 - Admin)
        frm_a = tk.Frame(frm_inferior, bg="#FFFFFF", bd=1, relief="solid", padx=15, pady=12)
        frm_a.pack(side="right", fill="both", expand=True, padx=(8, 0))
        tk.Label(frm_a, text="Reabastecimiento (Admin)", bg="#FFFFFF", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))

        tk.Label(frm_a, text="Cantidad que entra:", bg="#FFFFFF").pack(anchor="w")
        self.ent_a_cant = ttk.Entry(frm_a, width=15)
        self.ent_a_cant.pack(anchor="w", pady=(2, 6))

        tk.Label(frm_a, text="Costo unitario ($):", bg="#FFFFFF").pack(anchor="w")
        self.ent_a_costo = ttk.Entry(frm_a, width=15)
        self.ent_a_costo.pack(anchor="w", pady=(2, 8))

        estado_btn = "normal" if self.usuario_actual.rol == "Administrador" else "disabled"
        tk.Button(frm_a, text="➕ Sumar Stock", bg="#0284C7", fg="#FFFFFF", font=("Segoe UI", 9, "bold"), relief="flat", padx=10, state=estado_btn, command=self._evento_abastecer).pack(anchor="w")

        self._cargar_insumos_gui()

    def _cargar_insumos_gui(self):
        for r in self.tree_ins.get_children():
            self.tree_ins.delete(r)
        conn = GestorBaseDeDatos.obtener_conexion()
        for i in conn.execute("SELECT * FROM insumos").fetchall():
            obj = Insumo(i["id_insumo"], i["nombre_insumo"], i["stock_actual"], i["stock_minimo"], i["unidad_medida"], i["costo_promedio"])
            if obj.stockActual <= 0:
                tag, st = "ROJO", "ROJO - Agotado"
            elif obj.verificarAlertaStock():
                tag, st = "AMARILLO", "AMARILLO - Stock Crítico"
            else:
                tag, st = "VERDE", "VERDE - Óptimo"
            self.tree_ins.insert("", "end", values=(obj.idInsumo, obj.nombreInsumo, f"{obj.stockActual:.3f}", f"{obj.stockMinimo:.2f}", obj.unidadMedida, f"${obj.costoPromedio:.2f}", st), tags=(tag,))
        conn.close()

    def _evento_merma(self):
        sel = self.tree_ins.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un insumo de la tabla.")
            return
        try:
            id_ins = int(self.tree_ins.item(sel[0], "values")[0])
            m = Merma(id_ins, self.usuario_actual.idUsuario)
            m.registrarMerma(self.ent_m_cant.get(), self.cmb_m_motivo.get())
            messagebox.showinfo("Éxito", "Merma registrada correctamente.")
            self.ent_m_cant.delete(0, "end")
            self._cargar_insumos_gui()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _evento_abastecer(self):
        sel = self.tree_ins.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un insumo de la tabla.")
            return
        try:
            id_ins = int(self.tree_ins.item(sel[0], "values")[0])
            Insumo.abastecer_insumo(id_ins, self.ent_a_cant.get(), self.ent_a_costo.get())
            messagebox.showinfo("Éxito", "Abastecimiento registrado. Stock actualizado.")
            self.ent_a_cant.delete(0, "end")
            self.ent_a_costo.delete(0, "end")
            self._cargar_insumos_gui()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    # ========================================================================
    # VISTA 3: CORTE Y ARQUEO DE CAJA (RF-11)
    # ========================================================================
    def vista_corte_caja(self):
        tk.Label(self.content_area, text="Cierre de Turno y Arqueo Ciego", bg="#F1F5F9", fg="#0F172A", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 10))
        card = tk.Frame(self.content_area, bg="#FFFFFF", bd=1, relief="solid", padx=20, pady=20)
        card.pack(fill="x")

        tk.Label(card, text="Fondo Inicial ($):", bg="#FFFFFF", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", pady=5)
        self.ent_c_fondo = ttk.Entry(card, width=20)
        self.ent_c_fondo.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        self.ent_c_fondo.insert(0, "500.00")

        tk.Label(card, text="Efectivo Físico Contado ($):", bg="#FFFFFF", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.ent_c_efectivo = ttk.Entry(card, width=20)
        self.ent_c_efectivo.grid(row=1, column=1, sticky="w", padx=10, pady=5)

        tk.Button(card, text="🧮 Calcular y Guardar Corte", bg="#0284C7", fg="#FFFFFF", font=("Segoe UI", 10, "bold"), relief="flat", pady=8, command=self._evento_corte).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(15, 0))

        self.lbl_c_res = tk.Label(self.content_area, text="Realice el arqueo para ver el balance de caja.", bg="#FFFFFF", font=("Consolas", 10), bd=1, relief="solid", padx=15, pady=15, justify="left")
        self.lbl_c_res.pack(fill="x", pady=15)

    def _evento_corte(self):
        try:
            c = CorteCaja(self.usuario_actual.idUsuario, self.ent_c_fondo.get())
            res = c.realizarArqueo(self.ent_c_efectivo.get())
            self.lbl_c_res.config(text=f"Corte #{res['id_corte']} | Esperado: ${res['total_esperado']:,.2f} | Contado: ${res['efectivo_declarado']:,.2f}\nDiferencia: ${res['diferencia']:,.2f} -> {res['dictamen']}")
            messagebox.showinfo("Corte", res['dictamen'])
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    # ========================================================================
    # VISTA 4: HISTORIAL Y ANULACIONES (RF-06, RF-13)
    # ========================================================================
    def vista_historial(self):
        tk.Label(self.content_area, text="Historial de Órdenes y Visor PDF", bg="#F1F5F9", fg="#0F172A", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 10))

        cols = ("folio", "fecha", "pago", "total", "estado", "ruta")
        self.tree_hist = ttk.Treeview(self.content_area, columns=cols, show="headings", height=12)
        for c, t, w in [("folio", "Folio", 60), ("fecha", "Fecha", 150), ("pago", "Pago", 100), ("total", "Total", 90), ("estado", "Estado", 100), ("ruta", "Archivo PDF", 350)]:
            self.tree_hist.heading(c, text=t)
            self.tree_hist.column(c, width=w, anchor="center" if c != "ruta" else "w")
        self.tree_hist.pack(fill="x", pady=(0, 10))

        frm_h_btns = tk.Frame(self.content_area, bg="#F1F5F9")
        frm_h_btns.pack(anchor="w")

        tk.Button(frm_h_btns, text="📄 Abrir Comprobante PDF", bg="#0284C7", fg="#FFFFFF", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=6, command=self._evento_abrir_pdf).pack(side="left", padx=(0, 10))
        tk.Button(frm_h_btns, text="🔒 Anular Venta (Admin)", bg="#EF4444", fg="#FFFFFF", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=6, command=self._evento_anular).pack(side="left")

        self._cargar_historial_gui()

    def _cargar_historial_gui(self):
        for r in self.tree_hist.get_children(): self.tree_hist.delete(r)
        conn = GestorBaseDeDatos.obtener_conexion()
        filas = conn.execute("SELECT v.id_venta, v.fecha_hora, v.metodo_pago, v.total, v.estado, COALESCE(c.ruta_local, 'Sin PDF') AS ruta FROM ventas v LEFT JOIN comprobantes_pdf c ON v.id_venta = c.id_venta ORDER BY v.id_venta DESC").fetchall()
        conn.close()
        for f in filas:
            self.tree_hist.insert("", "end", values=(f["id_venta"], f["fecha_hora"], f["metodo_pago"], f"${f['total']:.2f}", f["estado"], f["ruta"]))

    def _evento_abrir_pdf(self):
        sel = self.tree_hist.selection()
        if not sel: return
        self._abrir_archivo_pdf(self.tree_hist.item(sel[0], "values")[5])

    def _evento_anular(self):
        sel = self.tree_hist.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una venta.")
            return
        folio = int(self.tree_hist.item(sel[0], "values")[0])
        pwd = simpledialog.askstring("Autorización", f"Contraseña del Administrador para anular el Folio #{folio:05d}:", show="*")
        if not pwd: return
        motivo = simpledialog.askstring("Motivo", "Escriba el motivo de la anulación:")
        if not motivo: return
        try:
            Venta.anular_venta_con_autorizacion(folio, pwd, motivo)
            messagebox.showinfo("Éxito", f"Venta #{folio:05d} anulada y stock revertido.")
            self._cargar_historial_gui()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    # ========================================================================
    # VISTAS DE ADMINISTRADOR (CATÁLOGO, REPORTES, USUARIOS)
    # ========================================================================
    def vista_catalogo(self):
        tk.Label(self.content_area, text="Catálogo de Productos y Recetas (RF-14)", bg="#F1F5F9", fg="#0F172A", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 10))
        card = tk.Frame(self.content_area, bg="#FFFFFF", bd=1, relief="solid", padx=15, pady=15)
        card.pack(fill="x")

        tk.Label(card, text="Nombre del Producto:", bg="#FFFFFF").grid(row=0, column=0, sticky="w", pady=4)
        self.ent_cat_nom = ttk.Entry(card, width=30)
        self.ent_cat_nom.grid(row=0, column=1, sticky="w", padx=5, pady=4)

        tk.Label(card, text="Categoría:", bg="#FFFFFF").grid(row=1, column=0, sticky="w", pady=4)
        self.cmb_cat_fam = ttk.Combobox(card, values=["Bebidas Calientes", "Bebidas Frías", "Repostería"], width=28, state="readonly")
        self.cmb_cat_fam.current(0)
        self.cmb_cat_fam.grid(row=1, column=1, sticky="w", padx=5, pady=4)

        tk.Label(card, text="Precio ($):", bg="#FFFFFF").grid(row=2, column=0, sticky="w", pady=4)
        self.ent_cat_pre = ttk.Entry(card, width=15)
        self.ent_cat_pre.grid(row=2, column=1, sticky="w", padx=5, pady=4)

        tk.Button(card, text="💾 Guardar Producto", bg="#10B981", fg="#FFFFFF", font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=6, command=self._evento_guardar_prod).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))

    def _evento_guardar_prod(self):
        try:
            Producto.registrar_nuevo_producto(self.ent_cat_nom.get(), self.cmb_cat_fam.get(), self.ent_cat_pre.get(), [(1, 0.018)])
            messagebox.showinfo("Éxito", "Producto agregado con receta estándar.")
            self.ent_cat_nom.delete(0, "end"); self.ent_cat_pre.delete(0, "end")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def vista_reportes(self):
        tk.Label(self.content_area, text="Generador de Reportes Gerenciales PDF (RF-12)", bg="#F1F5F9", fg="#0F172A", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 10))
        card = tk.Frame(self.content_area, bg="#FFFFFF", bd=1, relief="solid", padx=15, pady=15)
        card.pack(fill="x")
        hoy = datetime.now().strftime("%Y-%m-%d")

        tk.Label(card, text="Fecha Inicio (YYYY-MM-DD):", bg="#FFFFFF").grid(row=0, column=0, sticky="w", pady=5)
        self.ent_r_ini = ttk.Entry(card, width=15)
        self.ent_r_ini.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.ent_r_ini.insert(0, hoy)

        tk.Label(card, text="Fecha Fin (YYYY-MM-DD):", bg="#FFFFFF").grid(row=1, column=0, sticky="w", pady=5)
        self.ent_r_fin = ttk.Entry(card, width=15)
        self.ent_r_fin.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.ent_r_fin.insert(0, hoy)

        tk.Button(card, text="📊 Generar y Exportar Reporte PDF", bg="#0284C7", fg="#FFFFFF", font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=8, command=self._evento_rep).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))

    def _evento_rep(self):
        try:
            r = Reporte()
            d = r.generarReporteVentas(self.ent_r_ini.get(), self.ent_r_fin.get())
            pdf = r.exportarReportePDF()
            messagebox.showinfo("Reporte PDF", f"Órdenes: {d['num_ordenes']} | Total: ${d['total']:,.2f}\nGuardado en:\n{pdf}")
            self._abrir_archivo_pdf(pdf)
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def vista_usuarios(self):
        tk.Label(self.content_area, text="Gestión de Seguridad y Usuarios (RBAC)", bg="#F1F5F9", fg="#0F172A", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 10))

        cols = ("id", "usuario", "nombre", "rol", "estado")
        self.tree_usr = ttk.Treeview(self.content_area, columns=cols, show="headings", height=7)
        for c, t, w in [("id", "ID", 40), ("usuario", "Usuario", 130), ("nombre", "Nombre Completo", 200), ("rol", "Rol", 110), ("estado", "Estado", 130)]:
            self.tree_usr.heading(c, text=t)
            self.tree_usr.column(c, width=w, anchor="center" if c != "nombre" else "w")
        self.tree_usr.pack(fill="x", pady=(0, 10))

        card = tk.Frame(self.content_area, bg="#FFFFFF", bd=1, relief="solid", padx=15, pady=15)
        card.pack(fill="x")

        tk.Label(card, text="Usuario:", bg="#FFFFFF").grid(row=0, column=0, sticky="w", pady=4)
        self.ent_u_usr = ttk.Entry(card, width=20)
        self.ent_u_usr.grid(row=0, column=1, sticky="w", padx=5, pady=4)

        tk.Label(card, text="Nombre Completo:", bg="#FFFFFF").grid(row=0, column=2, sticky="w", pady=4, padx=(10, 0))
        self.ent_u_nom = ttk.Entry(card, width=25)
        self.ent_u_nom.grid(row=0, column=3, sticky="w", padx=5, pady=4)

        tk.Label(card, text="Contraseña:", bg="#FFFFFF").grid(row=1, column=0, sticky="w", pady=4)
        self.ent_u_pwd = ttk.Entry(card, width=20, show="*")
        self.ent_u_pwd.grid(row=1, column=1, sticky="w", padx=5, pady=4)

        tk.Label(card, text="Rol:", bg="#FFFFFF").grid(row=1, column=2, sticky="w", pady=4, padx=(10, 0))
        self.cmb_u_rol = ttk.Combobox(card, values=["Cajero", "Administrador"], state="readonly", width=23)
        self.cmb_u_rol.current(0)
        self.cmb_u_rol.grid(row=1, column=3, sticky="w", padx=5, pady=4)

        frm_b = tk.Frame(self.content_area, bg="#F1F5F9")
        frm_b.pack(fill="x", pady=10)
        tk.Button(frm_b, text="➕ Registrar Usuario", bg="#10B981", fg="#FFFFFF", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=6, command=self._evento_guarda_usr).pack(side="left", padx=(0, 10))
        tk.Button(frm_b, text="🔄 Activar / Desactivar", bg="#F59E0B", fg="#FFFFFF", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=6, command=self._evento_toggle_usr).pack(side="left")

        self._cargar_usuarios_gui()

    def _cargar_usuarios_gui(self):
        for r in self.tree_usr.get_children(): self.tree_usr.delete(r)
        for u in Usuario.obtener_todos_usuarios():
            st = "Activo" if u["activo"] == 1 else "Inactivo (Bloqueado)"
            self.tree_usr.insert("", "end", values=(u["id_usuario"], u["nombre_usuario"], u["nombre_completo"], u["rol"], st))

    def _evento_guarda_usr(self):
        try:
            Usuario.registrar_nuevo_usuario(self.ent_u_usr.get(), self.ent_u_nom.get(), self.cmb_u_rol.get(), self.ent_u_pwd.get())
            messagebox.showinfo("Éxito", "Usuario registrado correctamente.")
            self.ent_u_usr.delete(0, "end"); self.ent_u_nom.delete(0, "end"); self.ent_u_pwd.delete(0, "end")
            self._cargar_usuarios_gui()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _evento_toggle_usr(self):
        sel = self.tree_usr.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un usuario de la tabla.")
            return
        v = self.tree_usr.item(sel[0], "values")
        id_u, nom_u, est = int(v[0]), v[1], 1 if "Activo" in v[4] else 0
        if id_u == self.usuario_actual.idUsuario:
            messagebox.showerror("Error", "No puedes desactivar tu propio usuario en sesión.")
            return
        if messagebox.askyesno("Confirmar", f"¿Cambiar estado del usuario '{nom_u}'?"):
            Usuario.alternar_estado_usuario(id_u, est)
            self._cargar_usuarios_gui()


if __name__ == "__main__":
    app = AplicacionSICAVCafe()
    app.mainloop()