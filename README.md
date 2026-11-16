[README.md](https://github.com/user-attachments/files/34938261/README.md)
# Sistema Integral de Control Administrativo y Ventas (SICAV-Café)

**Documentación Técnica y Repositorio de Código Fuente**

El presente proyecto corresponde al desarrollo de un sistema de escritorio enfocado en la gestión operativa y administrativa de la Cafetería y Repostería Artesanal "Cielito Lindo". Su objetivo principal es sistematizar las transacciones en mostrador, eliminar la dependencia de impresoras térmicas mediante la emisión de comprobantes digitales (PDF) y asegurar la integridad del inventario a través de un modelo de deducción automática por recetas (escandallos).

## Características Principales

* **Control de Acceso (RBAC):** Implementación de perfiles de usuario (Administrador y Cajero) con segregación estricta de privilegios. Las contraseñas están resguardadas mediante funciones de hash criptográfico (SHA-256 + Salt).
* **Punto de Venta (POS):** Interfaz gráfica optimizada para el uso fluido de periféricos estándar (teclado y ratón). Incluye soporte para modificadores de productos con recálculo dinámico de costos y deducción de inventario.
* **Gestión de Inventario (Escandallo):** Deducción transaccional y atómica de materias primas fraccionadas (kilogramos, litros, piezas) conforme a recetas predefinidas en la base de datos.
* **Monitoreo de Existencias:** Sistema de alertas visuales codificadas por estado (Óptimo, Crítico, Agotado) con base en umbrales de stock mínimo para la prevención de desabasto.
* **Generación de Documentos PDF:** Compilación vectorial de notas de venta y reportes analíticos gerenciales de alto rendimiento utilizando la biblioteca `ReportLab`.
* **Integridad y Seguridad de Datos:** Aplicación de bajas lógicas para la gestión de usuarios, garantizando la conservación del historial de auditoría, e implementación de transacciones ACID para evitar inconsistencias operativas.

## Arquitectura y Tecnologías

* **Lenguaje de Programación:** Python 3.10+.
* **Base de Datos:** SQLite 3.
* **Interfaz Gráfica (GUI):** `tkinter` y `ttk`.
* **Motor PDF:** `reportlab`.
* **Seguridad Criptográfica:** `hashlib` (Librería estándar de Python).

## Estructura del Repositorio

```text
SICAV-Cafe/
├── BD_SICAV_Cafe.sql          # Script DDL/DML de la base de datos (3FN) y datos semilla
├── models_and_controllers.py  # Lógica de dominio (Clases UML, Validaciones y Transacciones)
├── main_gui.py                # Capa de presentación (Interfaz gráfica de escritorio)
├── requirements.txt           # Declaración de dependencias del entorno
└── comprobantes_pdf/          # Directorio autogenerado para persistencia de archivos PDF
```

## Instrucciones de Despliegue

1. **Clonación del repositorio:**
   ```bash
   git clone https://github.com/TU_USUARIO/SICAV-Cafe.git
   cd SICAV-Cafe
   ```

2. **Instalación de dependencias:**
   Se requiere la instalación del motor de renderizado para la generación de documentos PDF.
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecución del sistema:**
   La ejecución inicial compilará automáticamente el archivo `BD_SICAV_Cafe.db` a partir del script SQL, desplegando la base de datos relacional en el entorno local.
   ```bash
   python main_gui.py
   ```

## Credenciales de Acceso 

El sistema se inicializa con los siguientes usuarios precargados para propósitos de evaluación técnica y auditoría:

* **Perfil Administrador (Acceso Irrestricto):**
  * Usuario: `admin_roberto`
  * Contraseña: `admin123`

* **Perfil Cajero (Acceso Limitado a Operaciones POS):**
  * Usuario: `cajera_mariana`
  * Contraseña: `cajero123`

---
*Desarrollado por Mario Gustavo Trujillo Chua (Trujillo Software Solutions) como proyecto integrador para la asignatura de Ingeniería de Software.*
