"""
Proyecto: Sistema Integral de Control Administrativo y Ventas para Cafetería (SICAV-Café)
Organización: Cafetería y Repostería Artesanal "Cielito Lindo"
Autor: Mario Gustavo Trujillo Chua (Trujillo Software Solutions)
Descripción: Implementación de las clases del dominio, métodos documentados,
             validaciones del diccionario de datos, transacciones ACID
             en SQLite3 y generación de comprobantes/reportes en PDF.
"""

import os
import shutil
import sqlite3
import hashlib
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any

# Intentar importar ReportLab para generación vectorial de PDFs (RNF-02)
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_DISPONIBLE = True
except ImportError:
    REPORTLAB_DISPONIBLE = False


DB_FILENAME = "BD_SICAV_Cafe.db"
SQL_SCRIPT_FILE = "BD_SICAV_Cafe.sql"
CARPETA_PDF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "comprobantes_pdf")
SALT_SECRETO = "CielitoLindo_SICAV_2026_Salt"


class ValidadorDiccionarioDatos:
    """
    Clase utilitaria encargada de hacer cumplir las restricciones de tipos de datos
    y longitudes máximas estipuladas en el Diccionario de Datos (Lista de Cotejo).
    """

    @staticmethod
    def validar_cadena(valor: Any, nombre_campo: str, max_longitud: int) -> str:
        """
        Verifica que el dato sea una cadena de texto no vacía y que no exceda
        el tamaño máximo definido en el diccionario de datos.
        """
        if not isinstance(valor, str):
            raise ValueError(f"El campo '{nombre_campo}' requiere texto (Carácter).")
        texto_limpio = valor.strip()
        if len(texto_limpio) == 0:
            raise ValueError(f"El campo '{nombre_campo}' no puede estar vacío.")
        if len(texto_limpio) > max_longitud:
            raise ValueError(
                f"Error de Diccionario de Datos: El campo '{nombre_campo}' excede "
                f"el límite máximo de {max_longitud} caracteres (ingresado: {len(texto_limpio)})."
            )
        return texto_limpio

    @staticmethod
    def validar_numero_decimal(valor: Any, nombre_campo: str, permitir_cero: bool = False) -> float:
        """
        Verifica que el valor ingresado sea estrictamente numérico (DECIMAL/FLOAT),
        bloqueando la captura de letras o caracteres especiales.
        """
        try:
            if isinstance(valor, bool):
                raise ValueError()
            numero = float(valor)
        except (ValueError, TypeError):
            raise ValueError(
                f"Error de Diccionario de Datos: El campo '{nombre_campo}' espera un valor "
                f"Numérico (DECIMAL). No es posible ingresar letras ('{valor}')."
            )
        if permitir_cero and numero < 0:
            raise ValueError(f"El campo '{nombre_campo}' no puede ser negativo.")
        if not permitir_cero and numero <= 0:
            raise ValueError(f"El campo '{nombre_campo}' debe ser mayor a cero.")
        if numero >= 100000000.00:  # Límite DECIMAL(10,2)
            raise ValueError(f"El campo '{nombre_campo}' excede la precisión DECIMAL(10,2).")
        return round(numero, 3)

    @staticmethod
    def validar_entero(valor: Any, nombre_campo: str) -> int:
        """
        Verifica que el valor sea un número entero positivo (INT).
        """
        try:
            if isinstance(valor, bool) or (isinstance(valor, str) and "." in valor):
                raise ValueError()
            entero = int(valor)
        except (ValueError, TypeError):
            raise ValueError(
                f"Error de Diccionario de Datos: El campo '{nombre_campo}' espera un "
                f"número Entero (INT). Valor inválido: '{valor}'."
            )
        if entero <= 0:
            raise ValueError(f"El campo '{nombre_campo}' debe ser un entero positivo.")
        return entero


class GestorBaseDeDatos:
    """
    Gestiona la conexión local a SQLite3 con soporte transaccional ACID (RNF-08)
    y respaldos íntegros (RNF-10).
    """

    @staticmethod
    def obtener_conexion() -> sqlite3.Connection:
        conn = sqlite3.connect(DB_FILENAME)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @staticmethod
    def inicializar_bd() -> None:
        """
        Crea las 9 tablas normalizadas en 3FN y carga los usuarios y recetas semilla
        si la base de datos aún no existe en la computadora local.
        """
        os.makedirs(CARPETA_PDF, exist_ok=True)
        conn = GestorBaseDeDatos.obtener_conexion()
        with conn:
            if os.path.exists(SQL_SCRIPT_FILE):
                with open(SQL_SCRIPT_FILE, "r", encoding="utf-8") as f:
                    conn.executescript(f.read())
            else:
                # Respaldo DDL integrado en caso de ejecutar el script de forma aislada
                conn.executescript("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_usuario VARCHAR(50) NOT NULL UNIQUE,
                    nombre_completo VARCHAR(100) NOT NULL,
                    rol VARCHAR(20) NOT NULL,
                    contrasenia_hash VARCHAR(255) NOT NULL,
                    activo BOOLEAN NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS productos (
                    id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_producto VARCHAR(100) NOT NULL,
                    categoria VARCHAR(50) NOT NULL,
                    precio DECIMAL(10,2) NOT NULL,
                    disponible BOOLEAN NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS insumos (
                    id_insumo INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_insumo VARCHAR(100) NOT NULL,
                    stock_actual DECIMAL(10,2) NOT NULL,
                    stock_minimo DECIMAL(10,2) NOT NULL,
                    unidad_medida VARCHAR(20) NOT NULL,
                    costo_promedio DECIMAL(10,2) NOT NULL
                );
                CREATE TABLE IF NOT EXISTS recetas_producto (
                    id_receta INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_producto INTEGER NOT NULL,
                    id_insumo INTEGER NOT NULL,
                    cantidad_requerida DECIMAL(10,3) NOT NULL,
                    FOREIGN KEY (id_producto) REFERENCES productos(id_producto),
                    FOREIGN KEY (id_insumo) REFERENCES insumos(id_insumo)
                );
                CREATE TABLE IF NOT EXISTS ventas (
                    id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_usuario INTEGER NOT NULL,
                    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    subtotal DECIMAL(10,2) NOT NULL,
                    iva DECIMAL(10,2) NOT NULL,
                    total DECIMAL(10,2) NOT NULL,
                    metodo_pago VARCHAR(30) NOT NULL,
                    monto_recibido DECIMAL(10,2),
                    cambio_entregado DECIMAL(10,2),
                    estado VARCHAR(20) NOT NULL DEFAULT 'Completada',
                    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
                );
                CREATE TABLE IF NOT EXISTS detalle_ventas (
                    id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_venta INTEGER NOT NULL,
                    id_producto INTEGER NOT NULL,
                    cantidad INTEGER NOT NULL,
                    precio_unitario DECIMAL(10,2) NOT NULL,
                    subtotal DECIMAL(10,2) NOT NULL,
                    FOREIGN KEY (id_venta) REFERENCES ventas(id_venta),
                    FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
                );
                CREATE TABLE IF NOT EXISTS comprobantes_pdf (
                    id_comprobante INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_venta INTEGER NOT NULL UNIQUE,
                    nombre_archivo VARCHAR(150) NOT NULL,
                    ruta_local VARCHAR(255) NOT NULL,
                    fecha_generacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (id_venta) REFERENCES ventas(id_venta)
                );
                CREATE TABLE IF NOT EXISTS cortes_caja (
                    id_corte INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_usuario INTEGER NOT NULL,
                    fecha_apertura DATETIME NOT NULL,
                    fecha_cierre DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    fondo_inicial DECIMAL(10,2) NOT NULL,
                    total_calculado DECIMAL(10,2) NOT NULL,
                    efectivo_declarado DECIMAL(10,2) NOT NULL,
                    diferencia DECIMAL(10,2) NOT NULL,
                    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
                );
                CREATE TABLE IF NOT EXISTS mermas (
                    id_merma INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_insumo INTEGER NOT NULL,
                    id_usuario INTEGER NOT NULL,
                    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    cantidad DECIMAL(10,3) NOT NULL,
                    motivo VARCHAR(150) NOT NULL,
                    FOREIGN KEY (id_insumo) REFERENCES insumos(id_insumo),
                    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
                );
                """)

            # Asegurar usuarios iniciales con contraseñas cifradas (RNF-04)
            hash_admin = Usuario.cifrar_contrasenia("admin123")
            hash_cajero = Usuario.cifrar_contrasenia("cajero123")
            conn.execute("""
                INSERT OR IGNORE INTO usuarios (id_usuario, nombre_usuario, nombre_completo, rol, contrasenia_hash, activo)
                VALUES (1, 'admin_roberto', 'Lic. Roberto Morales Mendoza', 'Administrador', ?, 1)
            """, (hash_admin,))
            conn.execute("""
                INSERT OR IGNORE INTO usuarios (id_usuario, nombre_usuario, nombre_completo, rol, contrasenia_hash, activo)
                VALUES (2, 'cajera_mariana', 'Mariana Ruiz', 'Cajero', ?, 1)
            """, (hash_cajero,))
        conn.close()

    @staticmethod
    def respaldar_base_de_datos(ruta_destino: str) -> str:
        """
        RNF-10: Genera una copia de seguridad íntegra de la base de datos relacional.
        """
        shutil.copy2(DB_FILENAME, ruta_destino)
        return ruta_destino


# ============================================================================
# DOCUMENTACIÓN E IMPLEMENTACIÓN DE LAS 9 CLASES DEL DIAGRAMA DE CLASES UML
# ============================================================================

class Usuario:
    """
    Representa a un operador del sistema (Administrador o Cajero) y gestiona
    el control de acceso basado en roles (RBAC - RF-01).
    """

    def __init__(self, idUsuario: int = 0, nombreUsuario: str = "", nombreCompleto: str = "",
                 rol: str = "Cajero", contraseniaHash: str = "", activo: bool = True):
        self.idUsuario: int = idUsuario
        self.nombreUsuario: str = nombreUsuario
        self.nombreCompleto: str = nombreCompleto
        self.rol: str = rol
        self.contraseniaHash: str = contraseniaHash
        self.activo: bool = activo

    @staticmethod
    def obtener_todos_usuarios() -> list:
        """Retorna la lista de usuarios para mostrarlos en la interfaz."""
        conn = GestorBaseDeDatos.obtener_conexion()
        try:
            filas = conn.execute("SELECT id_usuario, nombre_usuario, nombre_completo, rol, activo FROM usuarios").fetchall()
        except sqlite3.OperationalError:
            filas = []
        finally:
            conn.close()
        return filas

    @staticmethod
    def registrar_nuevo_usuario(usr: str, nombre: str, rol: str, pwd_plana: str) -> None:
        """Inserta un nuevo usuario cifrando su contraseña primero."""
        usr_valido = ValidadorDiccionarioDatos.validar_cadena(usr, "nombre_usuario", 50)
        nom_valido = ValidadorDiccionarioDatos.validar_cadena(nombre, "nombre_completo", 100)
        pwd_valida = ValidadorDiccionarioDatos.validar_cadena(pwd_plana, "contrasenia", 255)
        
        hash_pwd = Usuario.cifrar_contrasenia(pwd_valida)
        conn = GestorBaseDeDatos.obtener_conexion()
        try:
            conn.execute("""
                INSERT INTO usuarios (nombre_usuario, nombre_completo, rol, contrasenia_hash, activo)
                VALUES (?, ?, ?, ?, 1)
            """, (usr_valido, nom_valido, rol, hash_pwd))
            conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError(f"El nombre de usuario '{usr_valido}' ya existe en el sistema.")
        finally:
            conn.close()

    @staticmethod
    def alternar_estado_usuario(id_usuario: int, estado_actual: int) -> None:
        """Baja/Alta Lógica: Cambia el estado (0 o 1) sin borrar el registro."""
        nuevo_estado = 0 if estado_actual == 1 else 1
        conn = GestorBaseDeDatos.obtener_conexion()
        with conn:
            conn.execute("UPDATE usuarios SET activo = ? WHERE id_usuario = ?", (nuevo_estado, id_usuario))
        conn.close()

    @staticmethod
    def cifrar_contrasenia(contrasenia_plana: str) -> str:
        """Aplica SHA-256 con salting para cumplir con el requisito RNF-04."""
        combinacion = f"{contrasenia_plana}{SALT_SECRETO}".encode("utf-8")
        return hashlib.sha256(combinacion).hexdigest()

    def iniciarSesion(self, usr: str, pass_plana: str) -> bool:
        """
        iniciarSesion(usr: String, pass: String): bool
        Este método valida el acceso al sistema. Recibe como argumentos el nombre
        de usuario y su contraseña encriptada. Retorna un valor booleano (Verdadero/Falso)
        indicando si las credenciales son válidas y habilita el menú según su rol.
        """
        nombreDeUsuario = ValidadorDiccionarioDatos.validar_cadena(usr, "nombre_usuario", 50)
        contraseniaValidar = ValidadorDiccionarioDatos.validar_cadena(pass_plana, "contrasenia_hash", 255)
        hash_calculado = self.cifrar_contrasenia(contraseniaValidar)

        conn = GestorBaseDeDatos.obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id_usuario, nombre_usuario, nombre_completo, rol, contrasenia_hash, activo
            FROM usuarios
            WHERE nombre_usuario = ? AND contrasenia_hash = ? AND activo = 1
        """, (nombreDeUsuario, hash_calculado))
        fila = cursor.fetchone()
        conn.close()

        if fila:
            self.idUsuario = fila["id_usuario"]
            self.nombreUsuario = fila["nombre_usuario"]
            self.nombreCompleto = fila["nombre_completo"]
            self.rol = fila["rol"]
            self.contraseniaHash = fila["contrasenia_hash"]
            self.activo = bool(fila["activo"])
            return True
        return False

    def cerrarSesion(self) -> None:
        """
        cerrarSesion(): void
        Este método finaliza la sesión activa del operador en curso, limpia las
        variables de memoria y bloquea la interfaz, regresando a la pantalla de inicio.
        """
        self.idUsuario = 0
        self.nombreUsuario = ""
        self.nombreCompleto = ""
        self.rol = ""
        self.contraseniaHash = ""
        self.activo = False

    @staticmethod
    def validar_credenciales_administrador(contrasenia_admin: str) -> Optional[int]:
        """
        Verifica la contraseña de un Administrador para autorizar cancelaciones (RF-06).
        Retorna el id_usuario del Administrador si es válida, o None en caso contrario.
        """
        hash_admin = Usuario.cifrar_contrasenia(contrasenia_admin.strip())
        conn = GestorBaseDeDatos.obtener_conexion()
        fila = conn.execute("""
            SELECT id_usuario FROM usuarios
            WHERE rol = 'Administrador' AND contrasenia_hash = ? AND activo = 1
        """, (hash_admin,)).fetchone()
        conn.close()
        return fila["id_usuario"] if fila else None


class Insumo:
    """
    Representa una materia prima en el almacén de la cafetería (RF-08, RF-09).
    """

    def __init__(self, idInsumo: int, nombreInsumo: str, stockActual: float,
                 stockMinimo: float, unidadMedida: str, costoPromedio: float):
        self.idInsumo: int = idInsumo
        self.nombreInsumo: str = ValidadorDiccionarioDatos.validar_cadena(nombreInsumo, "nombre_insumo", 100)
        self.stockActual: float = ValidadorDiccionarioDatos.validar_numero_decimal(stockActual, "stock_actual", permitir_cero=True)
        self.stockMinimo: float = ValidadorDiccionarioDatos.validar_numero_decimal(stockMinimo, "stock_minimo", permitir_cero=True)
        self.unidadMedida: str = ValidadorDiccionarioDatos.validar_cadena(unidadMedida, "unidad_medida", 20)
        self.costoPromedio: float = ValidadorDiccionarioDatos.validar_numero_decimal(costoPromedio, "costo_promedio", permitir_cero=True)

    def descontarStock(self, cantidad: float, cursor_transaccion: Optional[sqlite3.Cursor] = None) -> None:
        """
        descontarStock(cantidad: float): void
        Este método actualiza la base de datos restando la cantidad consumida
        (recibida como argumento) del stock físico actual de la materia prima.
        """
        cantidadRequerida = ValidadorDiccionarioDatos.validar_numero_decimal(cantidad, "cantidad_requerida")
        if self.stockActual < cantidadRequerida:
            raise ValueError(
                f"Stock insuficiente para '{self.nombreInsumo}'. "
                f"Disponible: {self.stockActual:.3f} {self.unidadMedida}, "
                f"Requerido: {cantidadRequerida:.3f} {self.unidadMedida}."
            )
        nuevoStock = round(self.stockActual - cantidadRequerida, 3)

        if cursor_transaccion is not None:
            cursor_transaccion.execute(
                "UPDATE insumos SET stock_actual = ? WHERE id_insumo = ?",
                (nuevoStock, self.idInsumo)
            )
        else:
            conn = GestorBaseDeDatos.obtener_conexion()
            with conn:
                conn.execute(
                    "UPDATE insumos SET stock_actual = ? WHERE id_insumo = ?",
                    (nuevoStock, self.idInsumo)
                )
            conn.close()
        self.stockActual = nuevoStock

    def verificarAlertaStock(self) -> bool:
        """
        verificarAlertaStock(): bool
        Este método evalúa si el inventario actual es menor o igual al límite
        configurado (stockMinimo). Retorna Verdadero si se debe emitir una
        advertencia visual en pantalla de desabasto.
        """
        return self.stockActual <= self.stockMinimo

    @staticmethod
    def abastecer_insumo(id_insumo: int, cantidad_entrada: Any, costo_compra_unitario: Any) -> None:
        """RF-09: Registra la entrada de materias primas y actualiza el stock y costo."""
        cantidadValida = ValidadorDiccionarioDatos.validar_numero_decimal(cantidad_entrada, "stock_actual")
        costoValido = ValidadorDiccionarioDatos.validar_numero_decimal(costo_compra_unitario, "costo_promedio")

        conn = GestorBaseDeDatos.obtener_conexion()
        with conn:
            conn.execute("""
                UPDATE insumos
                SET stock_actual = ROUND(stock_actual + ?, 3),
                    costo_promedio = ?
                WHERE id_insumo = ?
            """, (cantidadValida, costoValido, id_insumo))
        conn.close()


class RecetaProducto:
    """
    Representa un renglón del escandallo que vincula un Producto con un Insumo (RF-07).
    """

    def __init__(self, idReceta: int, idProducto: int, idInsumo: int, cantidadRequerida: float):
        self.idReceta: int = idReceta
        self.idProducto: int = idProducto
        self.idInsumo: int = idInsumo
        self.cantidadRequerida: float = ValidadorDiccionarioDatos.validar_numero_decimal(
            cantidadRequerida, "cantidad_requerida"
        )

    def obtenerCantidad(self) -> float:
        """
        obtenerCantidad(): float
        Este método consulta y retorna la cantidad exacta de materia prima que se
        necesita para preparar el producto (escandallo), dato que servirá para
        hacer el descuento en el inventario.
        """
        return self.cantidadRequerida


class Producto:
    """
    Representa un artículo comercial del catálogo de la cafetería (RF-02, RF-14).
    """

    def __init__(self, idProducto: int, nombreProducto: str, categoria: str,
                 precio: Any, disponible: bool = True):
        self.idProducto: int = idProducto
        self.nombreProducto: str = ValidadorDiccionarioDatos.validar_cadena(nombreProducto, "nombre_producto", 100)
        self.categoria: str = ValidadorDiccionarioDatos.validar_cadena(categoria, "categoria", 50)
        self.precio: float = ValidadorDiccionarioDatos.validar_numero_decimal(precio, "precio")
        self.disponible: bool = bool(disponible)

    def obtenerPrecio(self) -> float:
        """
        obtenerPrecio(): float
        Este método consulta y retorna el precio actual de venta al público del
        producto seleccionado para reflejarlo en la pantalla del cajero.
        """
        return self.precio

    @staticmethod
    def registrar_nuevo_producto(nombre: Any, categoria: Any, precio: Any,
                                 receta_items: List[Tuple[int, Any]]) -> int:
        """
        RF-14: Da de alta un nuevo platillo o bebida en la tabla productos junto
        con su receta (escandallo), validando estrictamente el diccionario de datos.
        """
        prod_validado = Producto(0, nombre, categoria, precio, True)
        conn = GestorBaseDeDatos.obtener_conexion()
        with conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO productos (nombre_producto, categoria, precio, disponible)
                VALUES (?, ?, ?, 1)
            """, (prod_validado.nombreProducto, prod_validado.categoria, prod_validado.precio))
            nuevo_id = cur.lastrowid

            for id_insumo, cant in receta_items:
                cant_valida = ValidadorDiccionarioDatos.validar_numero_decimal(cant, "cantidad_requerida")
                cur.execute("""
                    INSERT INTO recetas_producto (id_producto, id_insumo, cantidad_requerida)
                    VALUES (?, ?, ?)
                """, (nuevo_id, id_insumo, cant_valida))
        conn.close()
        return nuevo_id


class DetalleVenta:
    """
    Representa una partida individual dentro de una comanda activa (RF-02, RF-03).
    Soporta modificadores de bebidas (ej. Leche de Almendra +$12.00).
    """

    def __init__(self, idDetalle: int, idVenta: int, idProducto: int, nombreProducto: str,
                 cantidad: Any, precioUnitario: Any, descripcionModificador: str = "",
                 idInsumoExtra: Optional[int] = None, cantidadInsumoExtra: float = 0.0):
        self.idDetalle: int = idDetalle
        self.idVenta: int = idVenta
        self.idProducto: int = idProducto
        self.nombreProducto: str = nombreProducto
        self.cantidad: int = ValidadorDiccionarioDatos.validar_entero(cantidad, "cantidad")
        self.precioUnitario: float = ValidadorDiccionarioDatos.validar_numero_decimal(precioUnitario, "precio_unitario")
        self.descripcionModificador: str = descripcionModificador
        self.idInsumoExtra: Optional[int] = idInsumoExtra
        self.cantidadInsumoExtra: float = cantidadInsumoExtra
        self.subtotal: float = self.calcularSubtotal()

    def calcularSubtotal(self) -> float:
        """
        calcularSubtotal(): float
        Este método multiplica el atributo cantidad del producto seleccionado por
        su precioUnitario para obtener el subtotal de esa línea específica en la comanda.
        """
        self.subtotal = round(self.cantidad * self.precioUnitario, 2)
        return self.subtotal


class Venta:
    """
    Gestiona el ciclo completo de una transacción en mostrador: cálculo de IVA,
    validación de cobro, descuento atómico de inventario por receta y emisión de PDF.
    """

    def __init__(self):
        self.idVenta: int = 0
        self.idUsuario: int = 0
        self.fechaHora: str = ""
        self.subtotal: float = 0.0
        self.iva: float = 0.0
        self.total: float = 0.0
        self.metodoPago: str = "Efectivo"
        self.montoRecibido: float = 0.0
        self.cambio: float = 0.0
        self.estado: str = "Pendiente"
        self.detalles: List[DetalleVenta] = []
        self.rutaUltimoPDF: str = ""

    def crearVenta(self, idUser: int) -> None:
        """
        crearVenta(idUser: int): void
        Este método inicializa un nuevo folio de venta en blanco asociándolo al
        identificador del cajero en turno.
        """
        self.idVenta = 0
        self.idUsuario = ValidadorDiccionarioDatos.validar_entero(idUser, "id_usuario")
        self.fechaHora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.subtotal = 0.0
        self.iva = 0.0
        self.total = 0.0
        self.metodoPago = "Efectivo"
        self.montoRecibido = 0.0
        self.cambio = 0.0
        self.estado = "Pendiente"
        self.detalles.clear()
        self.rutaUltimoPDF = ""

    def agregarDetalle(self, detalle: DetalleVenta) -> None:
        """Agrega una línea a la comanda activa y recalcula el total."""
        self.detalles.append(detalle)
        self.calcularTotal()

    def calcularTotal(self) -> float:
        """
        calcularTotal(): float
        Este método recorre todos los productos agregados a la comanda (en DetalleVenta),
        suma sus costos, calcula el 16% de IVA y actualiza y retorna el importe total.
        """
        suma_partidas = sum(item.calcularSubtotal() for item in self.detalles)
        self.subtotal = round(suma_partidas / 1.16, 2)
        self.iva = round(suma_partidas - self.subtotal, 2)
        self.total = round(suma_partidas, 2)
        return self.total

    def procesarPago(self, monto: Any, metodo: str) -> bool:
        """
        procesarPago(monto: float, metodo: String): bool
        Este método recibe el dinero ingresado por teclado y el método de pago.
        Verifica que el monto cubra el importe total, calcula el cambio a devolver,
        descuenta insumos por receta en una transacción ACID y marca la venta como finalizada.
        """
        if not self.detalles:
            raise ValueError("La comanda está vacía. Agregue al menos un producto.")

        metodoPagoValido = ValidadorDiccionarioDatos.validar_cadena(metodo, "metodo_pago", 30)
        if metodoPagoValido not in ("Efectivo", "Tarjeta", "Transferencia"):
            raise ValueError("Método de pago inválido. Use: Efectivo, Tarjeta o Transferencia.")

        self.calcularTotal()

        if metodoPagoValido == "Efectivo":
            montoRecibido = ValidadorDiccionarioDatos.validar_numero_decimal(monto, "monto_recibido")
            if montoRecibido < self.total:
                raise ValueError(
                    f"Fondos insuficientes: El monto recibido (${montoRecibido:.2f}) "
                    f"es menor al total a pagar (${self.total:.2f})."
                )
            self.montoRecibido = montoRecibido
            self.cambio = round(montoRecibido - self.total, 2)
        else:
            # En pago con Tarjeta o Transferencia el cobro es exacto en terminal externa (Pregunta 22)
            self.montoRecibido = self.total
            self.cambio = 0.0

        self.metodoPago = metodoPagoValido
        self.fechaHora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Transacción ACID en Base de Datos (RNF-08)
        conn = GestorBaseDeDatos.obtener_conexion()
        try:
            with conn:
                cur = conn.cursor()
                # 1. Insertar cabecera de venta
                cur.execute("""
                    INSERT INTO ventas (
                        id_usuario, fecha_hora, subtotal, iva, total,
                        metodo_pago, monto_recibido, cambio_entregado, estado
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Completada')
                """, (
                    self.idUsuario, self.fechaHora, self.subtotal, self.iva,
                    self.total, self.metodoPago, self.montoRecibido, self.cambio
                ))
                self.idVenta = cur.lastrowid

                # 2. Insertar detalles y descontar stock por escandallo (RF-07)
                for item in self.detalles:
                    cur.execute("""
                        INSERT INTO detalle_ventas (
                            id_venta, id_producto, cantidad, precio_unitario, subtotal
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        self.idVenta, item.idProducto, item.cantidad,
                        item.precioUnitario, item.subtotal
                    ))

                    # Consultar receta del producto
                    recetas = cur.execute("""
                        SELECT r.id_receta, r.id_producto, r.id_insumo, r.cantidad_requerida,
                               i.nombre_insumo, i.stock_actual, i.stock_minimo, i.unidad_medida, i.costo_promedio
                        FROM recetas_producto r
                        JOIN insumos i ON r.id_insumo = i.id_insumo
                        WHERE r.id_producto = ?
                    """, (item.idProducto,)).fetchall()

                    for r in recetas:
                        receta_obj = RecetaProducto(r["id_receta"], r["id_producto"], r["id_insumo"], r["cantidad_requerida"])
                        insumo_obj = Insumo(
                            r["id_insumo"], r["nombre_insumo"], r["stock_actual"],
                            r["stock_minimo"], r["unidad_medida"], r["costo_promedio"]
                        )
                        consumo_total = round(receta_obj.obtenerCantidad() * item.cantidad, 3)
                        insumo_obj.descontarStock(consumo_total, cursor_transaccion=cur)

                    # Si tiene modificador extra (RF-03: ej. Leche de Almendra), descontar insumo adicional
                    if item.idInsumoExtra and item.cantidadInsumoExtra > 0:
                        ins_extra = cur.execute(
                            "SELECT * FROM insumos WHERE id_insumo = ?", (item.idInsumoExtra,)
                        ).fetchone()
                        if ins_extra:
                            insumo_mod_obj = Insumo(
                                ins_extra["id_insumo"], ins_extra["nombre_insumo"], ins_extra["stock_actual"],
                                ins_extra["stock_minimo"], ins_extra["unidad_medida"], ins_extra["costo_promedio"]
                            )
                            insumo_mod_obj.descontarStock(
                                round(item.cantidadInsumoExtra * item.cantidad, 3),
                                cursor_transaccion=cur
                            )

                self.estado = "Completada"
                # 3. Generar comprobante PDF y registrarlo en comprobantes_pdf (RF-05)
                self.rutaUltimoPDF = self.generarComprobantePDF(cursor_transaccion=cur)
            return True
        finally:
            conn.close()

    def generarComprobantePDF(self, cursor_transaccion: Optional[sqlite3.Cursor] = None) -> str:
        """
        generarComprobantePDF(): File (Ruta del archivo PDF generado)
        Este método recopila los datos de la transacción actual, formatea la nota
        de venta y genera el archivo físico en formato PDF en el disco duro.
        """
        os.makedirs(CARPETA_PDF, exist_ok=True)
        nombre_archivo = f"Nota_Venta_F{self.idVenta:05d}.pdf"
        ruta_completa = os.path.join(CARPETA_PDF, nombre_archivo)

        if REPORTLAB_DISPONIBLE:
            c = canvas.Canvas(ruta_completa, pagesize=letter)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, 750, "CAFETERÍA Y REPOSTERÍA ARTESANAL 'CIELITO LINDO'")
            c.setFont("Helvetica", 10)
            c.drawString(50, 735, "Sistema Integral de Control Administrativo y Ventas (SICAV-Café)")
            c.drawString(50, 720, "-" * 85)
            c.drawString(50, 705, f"Folio de Venta: #{self.idVenta:05d}          Fecha y Hora: {self.fechaHora}")
            c.drawString(50, 690, f"ID Operador en Caja: {self.idUsuario}             Método de Pago: {self.metodoPago}")
            c.drawString(50, 675, "-" * 85)

            y = 655
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y, "CANT.   DESCRIPCIÓN DEL PRODUCTO                          P. UNIT.     SUBTOTAL")
            y -= 15
            c.setFont("Helvetica", 10)

            for item in self.detalles:
                desc = item.nombreProducto
                if item.descripcionModificador:
                    desc += f" ({item.descripcionModificador})"
                c.drawString(50, y, f"{item.cantidad:<7} {desc[:45]:<47} ${item.precioUnitario:>7.2f}   ${item.subtotal:>8.2f}")
                y -= 16

            y -= 10
            c.drawString(50, y, "-" * 85)
            y -= 18
            c.drawString(350, y, f"SUBTOTAL:       ${self.subtotal:>8.2f} MXN")
            y -= 16
            c.drawString(350, y, f"IVA (16%):      ${self.iva:>8.2f} MXN")
            y -= 18
            c.setFont("Helvetica-Bold", 11)
            c.drawString(350, y, f"TOTAL PAGADO:   ${self.total:>8.2f} MXN")
            y -= 18
            c.setFont("Helvetica", 10)
            c.drawString(350, y, f"MONTO RECIBIDO: ${self.montoRecibido:>8.2f} MXN")
            y -= 16
            c.drawString(350, y, f"CAMBIO:         ${self.cambio:>8.2f} MXN")
            y -= 30
            c.setFont("Helvetica-Oblique", 9)
            c.drawString(50, y, "Comprobante digital emitido sin papel térmico - Trujillo Software Solutions.")
            c.save()
        else:
            # Respaldo en formato PDF básico si ReportLab aún no está instalado
            with open(ruta_completa, "w", encoding="utf-8") as f:
                f.write("CAFETERÍA Y REPOSTERÍA ARTESANAL 'CIELITO LINDO'\n")
                f.write(f"Folio: #{self.idVenta:05d} | Fecha: {self.fechaHora}\n")
                f.write(f"Método de Pago: {self.metodoPago}\n")
                f.write("-" * 60 + "\n")
                for item in self.detalles:
                    f.write(f"{item.cantidad} x {item.nombreProducto} ({item.descripcionModificador}) - ${item.subtotal:.2f}\n")
                f.write("-" * 60 + "\n")
                f.write(f"Subtotal: ${self.subtotal:.2f} | IVA (16%): ${self.iva:.2f} | TOTAL: ${self.total:.2f}\n")
                f.write(f"Recibido: ${self.montoRecibido:.2f} | Cambio: ${self.cambio:.2f}\n")

        if cursor_transaccion is not None:
            cursor_transaccion.execute("""
                INSERT INTO comprobantes_pdf (id_venta, nombre_archivo, ruta_local, fecha_generacion)
                VALUES (?, ?, ?, ?)
            """, (self.idVenta, nombre_archivo, ruta_completa, self.fechaHora))

        return ruta_completa

    @staticmethod
    def anular_venta_con_autorizacion(id_venta: Any, contrasenia_admin: str, motivo: str) -> None:
        """
        RF-06 / CU-10: Anula una venta previamente completada validando la contraseña
        del Administrador y revirtiendo los insumos descontados al almacén.
        """
        folioValido = ValidadorDiccionarioDatos.validar_entero(id_venta, "id_venta")
        motivoValido = ValidadorDiccionarioDatos.validar_cadena(motivo, "motivo_anulacion", 150)
        id_admin = Usuario.validar_credenciales_administrador(contrasenia_admin)
        if not id_admin:
            raise ValueError("Autorización denegada: Contraseña de Administrador incorrecta.")

        conn = GestorBaseDeDatos.obtener_conexion()
        with conn:
            cur = conn.cursor()
            venta_row = cur.execute("SELECT estado FROM ventas WHERE id_venta = ?", (folioValido,)).fetchone()
            if not venta_row:
                raise ValueError(f"No existe la venta con el folio #{folioValido}.")
            if venta_row["estado"] == "Cancelada":
                raise ValueError(f"La venta #{folioValido} ya se encuentra cancelada.")

            # Revertir insumos según detalle_ventas y recetas_producto
            detalles = cur.execute(
                "SELECT id_producto, cantidad FROM detalle_ventas WHERE id_venta = ?", (folioValido,)
            ).fetchall()

            for det in detalles:
                recetas = cur.execute(
                    "SELECT id_insumo, cantidad_requerida FROM recetas_producto WHERE id_producto = ?",
                    (det["id_producto"],)
                ).fetchall()
                for rec in recetas:
                    devolucion = round(rec["cantidad_requerida"] * det["cantidad"], 3)
                    cur.execute("""
                        UPDATE insumos
                        SET stock_actual = ROUND(stock_actual + ?, 3)
                        WHERE id_insumo = ?
                    """, (devolucion, rec["id_insumo"]))

            cur.execute("UPDATE ventas SET estado = 'Cancelada' WHERE id_venta = ?", (folioValido,))
        conn.close()


class Merma:
    """
    Gestiona las bajas justificadas de inventario por caducidad, derrame o calibración (RF-10).
    """

    def __init__(self, idInsumo: int, idUsuario: int):
        self.idMerma: int = 0
        self.idInsumo: int = ValidadorDiccionarioDatos.validar_entero(idInsumo, "id_insumo")
        self.idUsuario: int = ValidadorDiccionarioDatos.validar_entero(idUsuario, "id_usuario")
        self.fechaHora: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cantidad: float = 0.0
        self.motivo: str = ""

    def registrarMerma(self, cantidad: Any, motivo: str) -> bool:
        """
        registrarMerma(cantidad: float, motivo: String): bool
        Este método da de baja una cantidad de insumo del almacén (por caducidad,
        accidente, etc.) recibiendo la cantidad a descontar y el motivo, guardándolo
        en el registro sin considerarlo una venta comercial.
        """
        cantidadPerdida = ValidadorDiccionarioDatos.validar_numero_decimal(cantidad, "cantidad")
        motivoJustificado = ValidadorDiccionarioDatos.validar_cadena(motivo, "motivo", 150)

        conn = GestorBaseDeDatos.obtener_conexion()
        with conn:
            cur = conn.cursor()
            fila_ins = cur.execute("SELECT * FROM insumos WHERE id_insumo = ?", (self.idInsumo,)).fetchone()
            if not fila_ins:
                raise ValueError("El insumo seleccionado no existe.")

            insumo_obj = Insumo(
                fila_ins["id_insumo"], fila_ins["nombre_insumo"], fila_ins["stock_actual"],
                fila_ins["stock_minimo"], fila_ins["unidad_medida"], fila_ins["costo_promedio"]
            )
            insumo_obj.descontarStock(cantidadPerdida, cursor_transaccion=cur)

            cur.execute("""
                INSERT INTO mermas (id_insumo, id_usuario, fecha_hora, cantidad, motivo)
                VALUES (?, ?, ?, ?, ?)
            """, (self.idInsumo, self.idUsuario, self.fechaHora, cantidadPerdida, motivoJustificado))
            self.idMerma = cur.lastrowid
            self.cantidad = cantidadPerdida
            self.motivo = motivoJustificado
        conn.close()
        return True


class CorteCaja:
    """
    Gestiona la liquidación del turno mediante arqueo ciego de efectivo (RF-11).
    """

    def __init__(self, idUsuario: int, fondoInicial: Any = 500.00, fechaApertura: Optional[str] = None):
        self.idCorte: int = 0
        self.idUsuario: int = ValidadorDiccionarioDatos.validar_entero(idUsuario, "id_usuario")
        self.fechaApertura: str = fechaApertura or datetime.now().strftime("%Y-%m-%d 07:00:00")
        self.fechaCierre: str = ""
        self.fondoInicial: float = ValidadorDiccionarioDatos.validar_numero_decimal(
            fondoInicial, "fondo_inicial", permitir_cero=True
        )
        self.totalCalculado: float = 0.0
        self.efectivoDeclarado: float = 0.0
        self.diferencia: float = 0.0

    def realizarArqueo(self, efectivoDeclarado: Any) -> Dict[str, Any]:
        """
        realizarArqueo(efectivoDeclarado: float): void (retorna diccionario de resumen para GUI)
        Este método recibe la cantidad de dinero físico que el cajero contó. Suma el
        fondo inicial de la caja con las ventas en efectivo del turno y lo compara
        contra el efectivoDeclarado para calcular si hay un faltante o sobrante.
        """
        efectivoFisico = ValidadorDiccionarioDatos.validar_numero_decimal(
            efectivoDeclarado, "efectivo_declarado", permitir_cero=True
        )
        self.fechaCierre = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")

        conn = GestorBaseDeDatos.obtener_conexion()
        with conn:
            cur = conn.cursor()
            fila_ventas = cur.execute("""
                SELECT COALESCE(SUM(total), 0.0) AS suma_efectivo
                FROM ventas
                WHERE metodo_pago = 'Efectivo'
                  AND estado = 'Completada'
                  AND substr(fecha_hora, 1, 10) = ?
            """, (fecha_hoy,)).fetchone()

            ventas_efectivo_hoy = float(fila_ventas["suma_efectivo"])
            self.totalCalculado = round(self.fondoInicial + ventas_efectivo_hoy, 2)
            self.efectivoDeclarado = efectivoFisico
            self.diferencia = round(self.efectivoDeclarado - self.totalCalculado, 2)

            cur.execute("""
                INSERT INTO cortes_caja (
                    id_usuario, fecha_apertura, fecha_cierre, fondo_inicial,
                    total_calculado, efectivo_declarado, diferencia
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self.idUsuario, self.fechaApertura, self.fechaCierre,
                self.fondoInicial, self.totalCalculado, self.efectivoDeclarado, self.diferencia
            ))
            self.idCorte = cur.lastrowid
        conn.close()

        estado_corte = "CAJA CUADRADA EXACTA"
        if self.diferencia < 0:
            estado_corte = f"FALTANTE DE EFECTIVO (${abs(self.diferencia):.2f})"
        elif self.diferencia > 0:
            estado_corte = f"SOBRANTE DE EFECTIVO (+${self.diferencia:.2f})"

        return {
            "id_corte": self.idCorte,
            "fondo_inicial": self.fondoInicial,
            "ventas_efectivo": ventas_efectivo_hoy,
            "total_esperado": self.totalCalculado,
            "efectivo_declarado": self.efectivoDeclarado,
            "diferencia": self.diferencia,
            "dictamen": estado_corte
        }


class Reporte:
    """
    Consolida las métricas financieras y operativas por rango de fechas y las
    exporta a un documento PDF gerencial (RF-12).
    """

    def __init__(self):
        self.fechaInicio: str = ""
        self.fechaFin: str = ""
        self.datosConsolidados: Dict[str, Any] = {}

    def generarReporteVentas(self, fechaInicio: str, fechaFin: str) -> Dict[str, Any]:
        """
        generarReporteVentas(fechaInicio: Date, fechaFin: Date): void
        Este método consolida todas las ventas exitosas realizadas en el rango de
        fechas proporcionado como argumentos.
        """
        self.fechaInicio = ValidadorDiccionarioDatos.validar_cadena(fechaInicio, "fecha_inicio", 10)
        self.fechaFin = ValidadorDiccionarioDatos.validar_cadena(fechaFin, "fecha_fin", 10)

        conn = GestorBaseDeDatos.obtener_conexion()
        cur = conn.cursor()

        resumen_general = cur.execute("""
            SELECT COUNT(*) AS num_ordenes,
                   COALESCE(SUM(subtotal), 0.0) AS suma_subtotal,
                   COALESCE(SUM(iva), 0.0) AS suma_iva,
                   COALESCE(SUM(total), 0.0) AS suma_total
            FROM ventas
            WHERE estado = 'Completada'
              AND substr(fecha_hora, 1, 10) BETWEEN ? AND ?
        """, (self.fechaInicio, self.fechaFin)).fetchone()

        por_metodo = cur.execute("""
            SELECT metodo_pago, COUNT(*) AS cantidad, COALESCE(SUM(total), 0.0) AS monto
            FROM ventas
            WHERE estado = 'Completada'
              AND substr(fecha_hora, 1, 10) BETWEEN ? AND ?
            GROUP BY metodo_pago
        """, (self.fechaInicio, self.fechaFin)).fetchall()

        top_productos = cur.execute("""
            SELECT p.nombre_producto, SUM(d.cantidad) AS unidades, SUM(d.subtotal) AS ingreso
            FROM detalle_ventas d
            JOIN ventas v ON d.id_venta = v.id_venta
            JOIN productos p ON d.id_producto = p.id_producto
            WHERE v.estado = 'Completada'
              AND substr(v.fecha_hora, 1, 10) BETWEEN ? AND ?
            GROUP BY p.id_producto
            ORDER BY unidades DESC
        """, (self.fechaInicio, self.fechaFin)).fetchall()

        conn.close()

        self.datosConsolidados = {
            "rango": f"{self.fechaInicio} al {self.fechaFin}",
            "num_ordenes": resumen_general["num_ordenes"],
            "subtotal": float(resumen_general["suma_subtotal"]),
            "iva": float(resumen_general["suma_iva"]),
            "total": float(resumen_general["suma_total"]),
            "metodos": [dict(r) for r in por_metodo],
            "top_productos": [dict(r) for r in top_productos]
        }
        return self.datosConsolidados

    def exportarReportePDF(self) -> str:
        """
        exportarReportePDF(): File
        Toma los datos consolidados por el método anterior y los renderiza en un
        archivo PDF con formato estadístico y gerencial.
        """
        if not self.datosConsolidados:
            raise ValueError("Primero debe ejecutar generarReporteVentas(fechaInicio, fechaFin).")

        os.makedirs(CARPETA_PDF, exist_ok=True)
        marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_pdf = f"Reporte_Gerencial_{self.fechaInicio}_a_{self.fechaFin}_{marca_tiempo}.pdf"
        ruta_pdf = os.path.join(CARPETA_PDF, nombre_pdf)

        if REPORTLAB_DISPONIBLE:
            c = canvas.Canvas(ruta_pdf, pagesize=letter)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, 750, "REPORTE ANALÍTICO DE VENTAS - CAFETERÍA 'CIELITO LINDO'")
            c.setFont("Helvetica", 10)
            c.drawString(50, 732, f"Periodo auditado: {self.datosConsolidados['rango']}")
            c.drawString(50, 718, "-" * 85)

            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, 698, "1. RESUMEN FINANCIERO GLOBAL")
            c.setFont("Helvetica", 10)
            c.drawString(65, 680, f"Órdenes Completadas: {self.datosConsolidados['num_ordenes']}")
            c.drawString(65, 665, f"Subtotal Neto:       ${self.datosConsolidados['subtotal']:,.2f} MXN")
            c.drawString(65, 650, f"IVA Trasladado 16%:  ${self.datosConsolidados['iva']:,.2f} MXN")
            c.drawString(65, 635, f"INGRESO BRUTO TOTAL: ${self.datosConsolidados['total']:,.2f} MXN")

            y = 605
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y, "2. DESGLOSE POR MÉTODO DE PAGO")
            y -= 18
            c.setFont("Helvetica", 10)
            for m in self.datosConsolidados["metodos"]:
                c.drawString(65, y, f"- {m['metodo_pago']:<18}: {m['cantidad']} operaciones | Total: ${m['monto']:,.2f} MXN")
                y -= 15

            y -= 15
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y, "3. TOP DE PRODUCTOS MÁS VENDIDOS")
            y -= 18
            c.setFont("Helvetica", 10)
            for prod in self.datosConsolidados["top_productos"]:
                c.drawString(65, y, f"- {prod['nombre_producto']:<35}: {prod['unidades']} uds. | ${prod['ingreso']:,.2f} MXN")
                y -= 15

            c.save()
        else:
            with open(ruta_pdf, "w", encoding="utf-8") as f:
                f.write(f"REPORTE GERENCIAL CIELITO LINDO ({self.datosConsolidados['rango']})\n")
                f.write(f"Total Ventas: ${self.datosConsolidados['total']:,.2f} MXN\n")

        return ruta_pdf
