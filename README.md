# API de Gestión de Tareas

API REST para gestionar el ciclo de vida de tareas, construida con **FastAPI** y **SQLAlchemy**. Permite crear, consultar, actualizar parcialmente y eliminar tareas. Cada tarea posee un identificador único, título, descripción opcional, estado (`pending`, `in_progress`, `done`) y fecha de creación asignada automáticamente.

---

## Requisitos previos

| Requisito | Versión mínima |
|-----------|---------------|
| Python    | 3.12+         |
| pip       | 23+           |

No se requieren servicios externos; la API utiliza **SQLite** como base de datos local (archivo `tareas.db`).

## Dependencias principales

| Paquete     | Versión  | Propósito                          |
|-------------|----------|------------------------------------|
| FastAPI     | 0.136.1  | Framework web asíncrono            |
| SQLAlchemy  | 2.0.49   | ORM y gestión de base de datos     |
| Pydantic    | 2.13.4   | Validación y serialización de datos|
| Uvicorn     | 0.46.0   | Servidor ASGI                      |
| pytest      | 9.0.3    | Framework de tests                 |
| httpx       | 0.28.1   | Cliente HTTP para tests            |

---

## Instalación

1. **Clonar el repositorio:**

   ```bash
   git clone https://github.com/jmojpar/gestor-tareas-api-grupo-2.git
   cd gestor-tareas-api-grupo-2
   ```

2. **Crear y activar un entorno virtual:**

   ```bash
   python -m venv venv
   source venv/bin/activate        # macOS / Linux
   # venv\Scripts\activate          # Windows
   ```

3. **Instalar las dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

---

## Arrancar la aplicación

```bash
uvicorn aplicacion.principal:app --reload
```

La API estará disponible en `http://127.0.0.1:8000`.

La documentación interactiva (Swagger UI) se genera automáticamente en `http://127.0.0.1:8000/docs`.

---

## Endpoints

Todos los endpoints utilizan el prefijo `/tasks`.

### 1. Listar todas las tareas

| Campo  | Valor             |
|--------|-------------------|
| Método | `GET`             |
| Ruta   | `/tasks/`         |

**Parámetros:** ninguno.

**Ejemplo de petición:**

```bash
curl http://127.0.0.1:8000/tasks/
```

**Ejemplo de respuesta** (`200 OK`):

```json
[
  {
    "id": 1,
    "title": "Revisar documentación",
    "description": "Actualizar el README del proyecto",
    "status": "pending",
    "created_at": "2026-05-28T10:00:00"
  }
]
```

---

### 2. Obtener una tarea por id

| Campo  | Valor              |
|--------|--------------------|
| Método | `GET`              |
| Ruta   | `/tasks/{task_id}` |

**Parámetros de ruta:**

| Parámetro | Tipo  | Obligatorio | Descripción              |
|-----------|-------|-------------|--------------------------|
| `task_id` | `int` | sí          | Identificador de la tarea|

**Ejemplo de petición:**

```bash
curl http://127.0.0.1:8000/tasks/1
```

**Ejemplo de respuesta** (`200 OK`):

```json
{
  "id": 1,
  "title": "Revisar documentación",
  "description": "Actualizar el README del proyecto",
  "status": "pending",
  "created_at": "2026-05-28T10:00:00"
}
```

**Error** (`404 Not Found`):

```json
{
  "detail": "Task not found"
}
```

---

### 3. Crear una nueva tarea

| Campo  | Valor    |
|--------|----------|
| Método | `POST`   |
| Ruta   | `/tasks/`|

**Cuerpo de la petición (JSON):**

| Campo         | Tipo         | Obligatorio | Valor por defecto | Descripción                                          |
|---------------|--------------|-------------|-------------------|------------------------------------------------------|
| `title`       | `string`     | sí          | —                 | Título de la tarea                                   |
| `description` | `string`     | no          | `null`            | Descripción opcional                                 |
| `status`      | `string`     | no          | `"pending"`       | Estado inicial (`pending`, `in_progress` o `done`)   |

**Ejemplo de petición:**

```bash
curl -X POST http://127.0.0.1:8000/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Escribir tests", "description": "Cubrir los casos de error"}'
```

**Ejemplo de respuesta** (`201 Created`):

```json
{
  "id": 2,
  "title": "Escribir tests",
  "description": "Cubrir los casos de error",
  "status": "pending",
  "created_at": "2026-05-28T10:05:00"
}
```

---

### 4. Actualizar parcialmente una tarea

| Campo  | Valor              |
|--------|--------------------|
| Método | `PATCH`            |
| Ruta   | `/tasks/{task_id}` |

**Parámetros de ruta:**

| Parámetro | Tipo  | Obligatorio | Descripción              |
|-----------|-------|-------------|--------------------------|
| `task_id` | `int` | sí          | Identificador de la tarea|

**Cuerpo de la petición (JSON):** solo se incluyen los campos que se desean modificar.

| Campo         | Tipo         | Obligatorio | Descripción                                        |
|---------------|--------------|-------------|----------------------------------------------------|
| `title`       | `string`     | no          | Nuevo título                                       |
| `description` | `string`     | no          | Nueva descripción                                  |
| `status`      | `string`     | no          | Nuevo estado (`pending`, `in_progress` o `done`)   |

> **Restricciones:**
> - No se permite actualizar una tarea cuyo estado actual sea `done`.
> - El campo `title`, si se incluye, debe tener al menos 3 caracteres.

**Ejemplo de petición:**

```bash
curl -X PATCH http://127.0.0.1:8000/tasks/2 \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

**Ejemplo de respuesta** (`200 OK`):

```json
{
  "id": 2,
  "title": "Escribir tests",
  "description": "Cubrir los casos de error",
  "status": "in_progress",
  "created_at": "2026-05-28T10:05:00"
}
```

**Error** (`400 Bad Request` — tarea completada):

```json
{
  "detail": "Cannot update a completed task"
}
```

**Error** (`422 Unprocessable Entity` — título demasiado corto):

```json
{
  "detail": "Title must be at least 3 characters long"
}
```

**Error** (`404 Not Found`):

```json
{
  "detail": "Task not found"
}
```

---

### 5. Eliminar una tarea

| Campo  | Valor              |
|--------|--------------------|
| Método | `DELETE`           |
| Ruta   | `/tasks/{task_id}` |

**Parámetros de ruta:**

| Parámetro | Tipo  | Obligatorio | Descripción              |
|-----------|-------|-------------|--------------------------|
| `task_id` | `int` | sí          | Identificador de la tarea|

**Ejemplo de petición:**

```bash
curl -X DELETE http://127.0.0.1:8000/tasks/2
```

**Respuesta exitosa:** `204 No Content` (sin cuerpo).

**Error** (`404 Not Found`):

```json
{
  "detail": "Task not found"
}
```

---

### 6. Eliminar todas las tareas

| Campo  | Valor      |
|--------|------------|
| Método | `DELETE`   |
| Ruta   | `/tasks/`  |

**Parámetros:** ninguno.

**Ejemplo de petición:**

```bash
curl -X DELETE http://127.0.0.1:8000/tasks/
```

**Respuesta exitosa:** `204 No Content` (sin cuerpo). Todas las tareas han sido eliminadas de la base de datos.

---

## Ejecutar los tests

```bash
pytest tests/ -v
```

Los tests utilizan una base de datos SQLite independiente (`test_tareas.db`) para garantizar aislamiento. No afectan el archivo `tareas.db` de producción.

---

## Estructura del proyecto

```
gestor-tareas-api-grupo-2/
├── aplicacion/                 # Paquete principal de la aplicación
│   ├── principal.py            # Punto de entrada: instancia FastAPI y registro de routers
│   ├── base_de_datos.py        # Configuración del engine y sesión de SQLAlchemy
│   ├── modelos.py              # Modelos ORM (tabla tasks, enum TaskStatus)
│   ├── esquemas.py             # Esquemas Pydantic de entrada y respuesta
│   └── rutas/                  # Endpoints REST organizados por recurso
│       └── tareas.py           # Endpoints CRUD de tareas
├── tests/                      # Suite de tests con pytest
│   └── test_tasks.py           # Tests de integración de los endpoints
├── requirements.txt            # Dependencias del proyecto
├── AGENTS.md                   # Documentación técnica y reglas del sistema
├── .gitignore                  # Archivos y carpetas excluidos de Git
└── README.md                   # Este archivo
```
