-- ============================================================================
-- Nombre de Archivo: BD_SICAV_Cafe.sql
-- Fecha de creación: 18/09/2026
-- Descripción: Base de datos relacional normalizada (3FN) que contiene la
--              información transaccional, inventarios, recetas y control de
--              personal de la cafetería "Cielito Lindo" (SICAV-Café).
-- Autor: Mario Gustavo Trujillo Chua
-- ============================================================================

PRAGMA foreign_keys = ON;

-- 1. Tabla: usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_usuario VARCHAR(50) NOT NULL UNIQUE CHECK(length(nombre_usuario) <= 50),
    nombre_completo VARCHAR(100) NOT NULL CHECK(length(nombre_completo) <= 100),
    rol VARCHAR(20) NOT NULL CHECK(rol IN ('Administrador', 'Cajero') AND length(rol) <= 20),
    contrasenia_hash VARCHAR(255) NOT NULL CHECK(length(contrasenia_hash) <= 255),
    activo BOOLEAN NOT NULL DEFAULT 1 CHECK(activo IN (0, 1))
);

-- 2. Tabla: productos
CREATE TABLE IF NOT EXISTS productos (
    id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_producto VARCHAR(100) NOT NULL CHECK(length(nombre_producto) <= 100),
    categoria VARCHAR(50) NOT NULL CHECK(length(categoria) <= 50),
    precio DECIMAL(10,2) NOT NULL CHECK(precio >= 0),
    disponible BOOLEAN NOT NULL DEFAULT 1 CHECK(disponible IN (0, 1))
);

-- 3. Tabla: insumos
CREATE TABLE IF NOT EXISTS insumos (
    id_insumo INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_insumo VARCHAR(100) NOT NULL CHECK(length(nombre_insumo) <= 100),
    stock_actual DECIMAL(10,2) NOT NULL CHECK(stock_actual >= 0),
    stock_minimo DECIMAL(10,2) NOT NULL CHECK(stock_minimo >= 0),
    unidad_medida VARCHAR(20) NOT NULL CHECK(length(unidad_medida) <= 20),
    costo_promedio DECIMAL(10,2) NOT NULL CHECK(costo_promedio >= 0)
);

-- 4. Tabla: recetas_producto (Escandallo)
CREATE TABLE IF NOT EXISTS recetas_producto (
    id_receta INTEGER PRIMARY KEY AUTOINCREMENT,
    id_producto INTEGER NOT NULL,
    id_insumo INTEGER NOT NULL,
    cantidad_requerida DECIMAL(10,3) NOT NULL CHECK(cantidad_requerida > 0),
    FOREIGN KEY (id_producto) REFERENCES productos(id_producto) ON DELETE CASCADE,
    FOREIGN KEY (id_insumo) REFERENCES insumos(id_insumo) ON DELETE RESTRICT
);

-- 5. Tabla: ventas
CREATE TABLE IF NOT EXISTS ventas (
    id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL,
    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    subtotal DECIMAL(10,2) NOT NULL CHECK(subtotal >= 0),
    iva DECIMAL(10,2) NOT NULL CHECK(iva >= 0),
    total DECIMAL(10,2) NOT NULL CHECK(total >= 0),
    metodo_pago VARCHAR(30) NOT NULL CHECK(metodo_pago IN ('Efectivo', 'Tarjeta', 'Transferencia') AND length(metodo_pago) <= 30),
    monto_recibido DECIMAL(10,2),
    cambio_entregado DECIMAL(10,2),
    estado VARCHAR(20) NOT NULL DEFAULT 'Completada' CHECK(estado IN ('Completada', 'Cancelada') AND length(estado) <= 20),
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);

-- 6. Tabla: detalle_ventas
CREATE TABLE IF NOT EXISTS detalle_ventas (
    id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
    id_venta INTEGER NOT NULL,
    id_producto INTEGER NOT NULL,
    cantidad INTEGER NOT NULL CHECK(cantidad > 0),
    precio_unitario DECIMAL(10,2) NOT NULL CHECK(precio_unitario >= 0),
    subtotal DECIMAL(10,2) NOT NULL CHECK(subtotal >= 0),
    FOREIGN KEY (id_venta) REFERENCES ventas(id_venta) ON DELETE CASCADE,
    FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
);

-- 7. Tabla: comprobantes_pdf
CREATE TABLE IF NOT EXISTS comprobantes_pdf (
    id_comprobante INTEGER PRIMARY KEY AUTOINCREMENT,
    id_venta INTEGER NOT NULL UNIQUE,
    nombre_archivo VARCHAR(150) NOT NULL CHECK(length(nombre_archivo) <= 150),
    ruta_local VARCHAR(255) NOT NULL CHECK(length(ruta_local) <= 255),
    fecha_generacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_venta) REFERENCES ventas(id_venta) ON DELETE CASCADE
);

-- 8. Tabla: cortes_caja
CREATE TABLE IF NOT EXISTS cortes_caja (
    id_corte INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL,
    fecha_apertura DATETIME NOT NULL,
    fecha_cierre DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fondo_inicial DECIMAL(10,2) NOT NULL CHECK(fondo_inicial >= 0),
    total_calculado DECIMAL(10,2) NOT NULL CHECK(total_calculado >= 0),
    efectivo_declarado DECIMAL(10,2) NOT NULL CHECK(efectivo_declarado >= 0),
    diferencia DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);

-- 9. Tabla: mermas
CREATE TABLE IF NOT EXISTS mermas (
    id_merma INTEGER PRIMARY KEY AUTOINCREMENT,
    id_insumo INTEGER NOT NULL,
    id_usuario INTEGER NOT NULL,
    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cantidad DECIMAL(10,3) NOT NULL CHECK(cantidad > 0),
    motivo VARCHAR(150) NOT NULL CHECK(length(motivo) <= 150),
    FOREIGN KEY (id_insumo) REFERENCES insumos(id_insumo),
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);

-- ============================================================================
-- DATOS SEMILLA INICIALES (Cafetería "Cielito Lindo")
-- Nota: Las contraseñas se inicializan desde Python con SHA-256 + Salt:
--       admin_roberto -> "admin123"
--       cajera_mariana -> "cajero123"
-- ============================================================================

INSERT OR IGNORE INTO insumos (id_insumo, nombre_insumo, stock_actual, stock_minimo, unidad_medida, costo_promedio) VALUES
(1, 'Café en Grano Especialidad', 8.50, 2.00, 'kg', 340.00),
(2, 'Leche Entera Pasteurizada', 18.00, 5.00, 'litros', 26.50),
(3, 'Leche de Almendra (Modificador)', 4.20, 3.00, 'litros', 52.00),
(4, 'Vaso Desechable con Tapa 12oz', 150.00, 30.00, 'piezas', 2.80),
(5, 'Jarabe de Vainilla / Avellana', 1.80, 2.00, 'litros', 185.00),
(6, 'Rebanada Pastel Artesanal', 14.00, 4.00, 'piezas', 35.00);

INSERT OR IGNORE INTO productos (id_producto, nombre_producto, categoria, precio, disponible) VALUES
(1, 'Cappuccino Mediano', 'Bebidas Calientes', 58.00, 1),
(2, 'Café Americano Grande', 'Bebidas Calientes', 42.00, 1),
(3, 'Latte Frappé Artesanal', 'Bebidas Frías', 68.00, 1),
(4, 'Pastel de Chocolate Cielito Lindo', 'Repostería', 75.00, 1);

-- Escandallo exacto (Pregunta 10 de la entrevista: Cappuccino = 18g café, 220ml leche, 1 vaso)
INSERT OR IGNORE INTO recetas_producto (id_receta, id_producto, id_insumo, cantidad_requerida) VALUES
(1, 1, 1, 0.018), -- 18 gramos de café
(2, 1, 2, 0.220), -- 220 ml de leche
(3, 1, 4, 1.000), -- 1 vaso con tapa
(4, 2, 1, 0.020), -- 20 gramos de café
(5, 2, 4, 1.000), -- 1 vaso con tapa
(6, 3, 1, 0.018), -- 18 gramos de café
(7, 3, 2, 0.250), -- 250 ml de leche
(8, 3, 5, 0.030), -- 30 ml jarabe
(9, 3, 4, 1.000), -- 1 vaso con tapa
(10, 4, 6, 1.000); -- 1 rebanada de pastel