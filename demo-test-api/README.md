# Demo Test API - Alumnos

API REST simple desarrollada con FastAPI y SQLite para pruebas de carga.

## Entidad Alumno

La entidad `Alumno` contiene los siguientes campos:
- `id` (int): Identificador único autoincremental
- `nombre` (str): Nombre del alumno
- `apellido` (str): Apellido del alumno
- `edad` (int): Edad del alumno
- `email` (str): Email único del alumno
- `carrera` (str): Carrera que cursa el alumno

## Endpoints disponibles

### Health Check
- `GET /` - Información básica de la API
- `GET /health` - Estado de salud del servicio

### CRUD de Alumnos
- `POST /alumnos` - Crear un nuevo alumno
- `GET /alumnos` - Listar alumnos (con paginación: skip, limit)
- `GET /alumnos/{alumno_id}` - Obtener un alumno por ID
- `PUT /alumnos/{alumno_id}` - Actualizar un alumno
- `DELETE /alumnos/{alumno_id}` - Eliminar un alumno

## Ejecución

### Con Docker Compose (desde la raíz del proyecto)
```bash
docker-compose up demo_test_api
```

La API estará disponible en: `http://localhost:8020`

### Localmente
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Documentación interactiva

Una vez levantado el servicio, puedes acceder a:
- Swagger UI: `http://localhost:8020/docs`
- ReDoc: `http://localhost:8020/redoc`

## Ejemplo de uso

### Crear un alumno
```bash
curl -X POST "http://localhost:8020/alumnos" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan",
    "apellido": "Pérez",
    "edad": 22,
    "email": "juan.perez@example.com",
    "carrera": "Ingeniería Informática"
  }'
```

### Listar alumnos
```bash
curl "http://localhost:8020/alumnos"
```

### Obtener un alumno
```bash
curl "http://localhost:8020/alumnos/1"
```

### Actualizar un alumno
```bash
curl -X PUT "http://localhost:8020/alumnos/1" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan Carlos",
    "apellido": "Pérez",
    "edad": 23,
    "email": "juan.perez@example.com",
    "carrera": "Ingeniería Informática"
  }'
```

### Eliminar un alumno
```bash
curl -X DELETE "http://localhost:8020/alumnos/1"
```

## Base de datos

La base de datos SQLite se crea automáticamente al iniciar la aplicación. Los datos se persisten en el volumen `./demo-test-api/data/` cuando se ejecuta con Docker.
