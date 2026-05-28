# ADR-001: Elección de SQLite como base de datos

## Estado

**Aceptado**

## Contexto

La API de Gestión de Tareas necesita una base de datos relacional para persistir tareas con campos estructurados (`id`, `title`, `description`, `status`, `created_at`). El proyecto está concebido como una API REST educativa y de pequeña escala, desplegable con un único proceso Python (Uvicorn) y sin infraestructura externa.

Los requisitos clave que condicionan la decisión son:

- **Cero dependencias de infraestructura**: el equipo necesita poder clonar el repositorio y ejecutar la API sin instalar ni configurar un servidor de base de datos.
- **Simplicidad operativa**: no se requiere alta disponibilidad, replicación ni acceso concurrente intensivo.
- **Compatibilidad con SQLAlchemy 2.0**: el ORM elegido debe poder conectarse a la base de datos sin adaptadores adicionales.
- **Soporte nativo en Python**: la librería estándar de Python incluye el módulo `sqlite3`, lo que elimina dependencias binarias externas.
- **Facilidad para tests**: los tests necesitan una base de datos aislada y efímera que no afecte los datos de desarrollo.

## Decisión

Se adopta **SQLite** como motor de base de datos, almacenando los datos en el archivo local `tareas.db`. Para los tests se utiliza SQLite en memoria con `StaticPool`, garantizando aislamiento total respecto a los datos de desarrollo.

### Razones principales

1. **Sin servidor**: SQLite es una base de datos embebida; no requiere un proceso daemon, puerto de red ni configuración de usuarios o permisos.
2. **Portabilidad total**: el archivo `tareas.db` se puede copiar, respaldar o eliminar como cualquier archivo. Toda la base de datos viaja con el proyecto.
3. **Incluida en la librería estándar**: Python incorpora `sqlite3` de serie, por lo que no se necesita instalar drivers adicionales (a diferencia de `psycopg2` o `mysqlclient`).
4. **Rendimiento suficiente**: para el volumen de datos esperado (cientos o pocos miles de tareas), SQLite ofrece tiempos de respuesta excelentes sin necesidad de optimización.
5. **Tests inmediatos**: `sqlite:///:memory:` con `StaticPool` permite crear y destruir bases de datos en memoria en milisegundos, acelerando la suite de tests.
6. **Compatibilidad con SQLAlchemy**: la cadena de conexión `sqlite:///tareas.db` funciona directamente con SQLAlchemy 2.0 sin configuración adicional.

## Alternativas consideradas

### PostgreSQL

| Aspecto | Evaluación |
|---|---|
| **Ventajas** | Motor robusto de nivel empresarial. Soporte avanzado de tipos (JSON, arrays, UUID nativo). Excelente rendimiento en concurrencia alta. Extensiones como PostGIS. Ideal para producción a gran escala. |
| **Inconvenientes** | Requiere instalar y configurar un servidor PostgreSQL (o usar Docker). Añade una dependencia externa (`psycopg2` o `asyncpg`) con compilación nativa. Configuración de usuarios, contraseñas y permisos. Incrementa significativamente la complejidad del entorno de desarrollo y despliegue para un proyecto de este alcance. |

### MySQL

| Aspecto | Evaluación |
|---|---|
| **Ventajas** | Motor maduro y ampliamente adoptado. Buen rendimiento en operaciones de lectura. Amplio ecosistema de herramientas de administración (phpMyAdmin, MySQL Workbench). Soporte comercial a través de Oracle. |
| **Inconvenientes** | Requiere un servidor MySQL corriendo como servicio. Necesita el driver `mysqlclient` o `PyMySQL`, que pueden presentar problemas de instalación en ciertos entornos. Menor riqueza de tipos comparado con PostgreSQL. Licenciamiento dual (GPL / comercial) que puede generar dudas en algunos contextos. Complejidad innecesaria para el volumen y concurrencia de este proyecto. |

## Consecuencias

### Positivas

- **Arranque inmediato**: cualquier desarrollador puede ejecutar `pip install -r requirements.txt` y tener la API funcionando sin pasos adicionales de infraestructura.
- **Tests rápidos y aislados**: la suite de tests se ejecuta en milisegundos usando bases de datos en memoria, sin riesgo de colisión con datos reales.
- **Despliegue simplificado**: un único artefacto (el código Python + el archivo `.db`) es suficiente para ejecutar la aplicación.
- **Bajo coste cognitivo**: los nuevos miembros del equipo no necesitan aprender a administrar un SGBD externo.

### Negativas y riesgos a largo plazo

- **Concurrencia limitada**: SQLite utiliza un bloqueo a nivel de archivo para escrituras. Si la aplicación crece y recibe muchas escrituras simultáneas, se convertirá en un cuello de botella. En ese escenario sería necesario migrar a PostgreSQL.
- **Sin acceso remoto nativo**: SQLite no expone un protocolo de red. Si múltiples servicios o réplicas necesitan acceder a la misma base de datos, SQLite no es viable.
- **Funcionalidades SQL reducidas**: SQLite no soporta algunas características avanzadas de SQL como `ALTER COLUMN`, tipos estrictos (sin modo estricto), o procedimientos almacenados. Esto podría limitar migraciones de esquema complejas en el futuro.
- **Migración futura**: si el proyecto escala, la migración a PostgreSQL requerirá cambiar la cadena de conexión de SQLAlchemy, instalar el driver correspondiente y, potencialmente, ajustar consultas que dependan de comportamientos específicos de SQLite (por ejemplo, tipado dinámico o manejo de fechas).
- **No apto para alta disponibilidad**: no hay soporte nativo para replicación, failover ni backups en caliente, lo cual es imprescindible en entornos de producción críticos.

### Mitigaciones previstas

- La capa ORM (SQLAlchemy) abstrae el dialecto SQL, facilitando una futura migración con cambios mínimos en el código.
- Se evita el uso de funcionalidades exclusivas de SQLite en las consultas para mantener la portabilidad.
- Si el proyecto supera las capacidades de SQLite, se documentará una nueva ADR para la migración a PostgreSQL.
