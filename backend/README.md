# 🚀 LoadTester

**Automated API Load Testing with OpenAPI Specification**

LoadTester es una aplicación web que permite realizar pruebas de carga automáticas en APIs a partir de documentos OpenAPI Specification (OAS). La aplicación genera escenarios de prueba incrementales, ejecuta tests con K6 y produce reportes profesionales en PDF.

## ✨ **Características Principales**

- 📋 **Parsing OpenAPI 3.0+** - Carga especificaciones vía URL o texto
- 🎯 **Selección de Endpoints** - Configura qué endpoints testear
- 🔐 **Autenticación** - Soporte para Bearer Token y API Key
- 🤖 **Datos Mock Automáticos** - Generación inteligente con IA
- 📊 **Escalado Incremental** - Detecta puntos de degradación automáticamente
- 📈 **Reportes PDF** - Gráficos profesionales y análisis ejecutivo
- 🔄 **API Asíncrona** - Long-jobs con seguimiento de estado
- 🐳 **Docker Compose** - Despliegue completo con un comando

## 🏗️ **Arquitectura**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │      K6         │
│   (Streamlit)   │───▶│   (FastAPI)     │───▶│  Load Testing   │
│   Port: 8501    │    │   Port: 8000    │    │   Framework     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   SQLite DB     │
                       │   (Persistent)  │
                       └─────────────────┘
```

### **Stack Tecnológico**
- **Frontend**: Streamlit (Interfaz minimalista)
- **Backend**: FastAPI (Arquitectura en 3 capas)
- **Base de Datos**: SQLite (Persistente con volúmenes)
- **Load Testing**: K6 (Contenedor separado)
- **IA**: Google Gemini / Anthropic Claude (APIs gratuitas)
- **Reportes**: ReportLab + Matplotlib
- **Orquestación**: Docker Compose

## 🚀 **Inicio Rápido**

### **Prerrequisitos**
- Docker y Docker Compose
- Python 3.11+ (para desarrollo)
- UV package manager

### **1. Clonar y Configurar**
```bash
git clone <repository>
cd loadtester

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys de IA
```

### **2. Configurar API Keys**
Edita el archivo `.env` y añade al menos una API key:
```bash
# Al menos una de estas es requerida:
GOOGLE_API_KEY=tu_google_gemini_api_key
ANTHROPIC_API_KEY=tu_anthropic_api_key
```

### **3. Crear Directorios**
```bash
# Crear estructura de directorios
mkdir -p shared/{database,data/uploads,data/mocked,reports/generated}
mkdir -p k6/{scripts/generated,results/generated}
```

### **4. Levantar Servicios**
```bash
docker-compose up --build
```

### **5. Acceder a la Aplicación**
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs

## 📖 **Cómo Usar LoadTester**

### **Paso 1: Cargar OpenAPI Specification**
1. Abre http://localhost:8501
2. Introduce tu documento OAS:
   - **URL**: `https://petstore.swagger.io/v2/swagger.json`
   - **Texto**: Copia/pega tu JSON/YAML

### **Paso 2: Seleccionar Endpoints**
1. Selecciona los endpoints que quieres testear
2. Configura para cada endpoint:
   - Tipo de autenticación (Bearer Token / API Key)
   - Volumetría esperada (requests/min)
   - Usuarios concurrentes
   - Datos de prueba (archivo o automático)

### **Paso 3: Configurar Autenticación**
```bash
# Configuración global o por endpoint
Bearer Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
API Key: sk-1234567890abcdef...
```

### **Paso 4: Ejecutar Prueba**
1. Haz clic en "Iniciar Prueba de Carga"
2. Recibirás un Job ID para seguimiento
3. El sistema escalará automáticamente hasta detectar degradación

### **Paso 5: Descargar Reporte**
1. Una vez finalizada, descarga el reporte PDF
2. El reporte incluye gráficos de rendimiento y puntos de degradación

## 📊 **Criterios de Degradación**

LoadTester detecta degradación usando estos umbrales configurables:

- **Tiempo de Respuesta**: >500% del tiempo base del primer escenario
- **Tasa de Error**: >50% de peticiones fallan
- **Escalado**: Comienza con 10% usuarios, incrementa 50% cada iteración
- **Parada**: Cuando 60% de peticiones fallan

## 🔧 **Desarrollo**

### **Arquitectura Backend (3 Capas)**

```
app/
├── presentation/     # Controllers, API routes, middleware
├── domain/          # Business logic, entities, interfaces
└── infrastructure/  # Database, external services, repositories
```

### **Comandos de Desarrollo**
```bash
# Instalar dependencias con UV
uv sync

# Ejecutar tests
uv run pytest

# Formatear código
uv run black .
uv run isort .

# Type checking
uv run mypy .

# Ejecutar backend en desarrollo
uv run uvicorn app.main:app --reload --port 8000

# Ejecutar frontend en desarrollo
streamlit run frontend/app.py --server.port 8501
```

### **Testing**
```bash
# Tests unitarios
uv run pytest backend/app/tests/unit/

# Tests de integración
uv run pytest backend/app/tests/integration/

# Coverage
uv run pytest --cov=app --cov-report=html
```

## 📁 **Estructura de Datos**

### **Archivos de Datos Personalizados**

#### **Formato CSV**
```csv
path_param1,path_param2,query_param1,body_json
1001,active,category=electronics,"{\"name\":\"Product1\",\"price\":99.99}"
1002,inactive,category=books,"{\"name\":\"Product2\",\"price\":19.99}"
```

#### **Formato JSON**
```json
[
  {
    "path_params": {"id": 1001, "status": "active"},
    "query_params": {"category": "electronics"},
    "body": {"name": "Product1", "price": 99.99}
  }
]
```

### **Datos Mock Automáticos**
La IA genera automáticamente datos realistas basados en:
- Esquemas OpenAPI
- Tipos de datos especificados
- Formatos (email, fecha, UUID, etc.)
- Restricciones de validación

## 🔄 **API Backend**

### **Endpoints Principales**

#### **Crear Prueba de Carga**
```bash
POST /api/v1/load-test
Content-Type: application/json

{
  "openapi_spec": "...",
  "endpoints": [...],
  "global_auth": {...},
  "callback_url": "https://your-app.com/webhook"
}

Response: {"job_id": "uuid", "status_url": "/api/v1/status/{job_id}"}
```

#### **Consultar Estado**
```bash
GET /api/v1/status/{job_id}

Response: {
  "status": "RUNNING",
  "progress": 45,
  "report_url": null
}
```

#### **Descargar Reporte**
```bash
GET /api/v1/report/{job_id}

Response: PDF file
```

## 🐳 **Docker Services**

### **Servicios Incluidos**
- **loadtester-backend**: FastAPI application
- **loadtester-frontend**: Streamlit interface  
- **loadtester-k6**: K6 load testing engine

### **Volúmenes Persistentes**
- `./shared/database`: Base de datos SQLite
- `./shared/data`: Archivos subidos y datos mock
- `./shared/reports`: Reportes PDF generados
- `./k6/scripts`: Scripts K6 generados
- `./k6/results`: Resultados de ejecución

## 🤖 **Integración con IA**

LoadTester utiliza servicios de IA para:

1. **Parsing OpenAPI**: Interpretar especificaciones complejas
2. **Generación Mock**: Crear datos de prueba realistas
3. **Generación K6**: Convertir configuración a scripts K6
4. **Reportes**: Análisis inteligente de resultados

### **Servicios Soportados**
- Google Gemini (gratuito)
- Anthropic Claude (free tier)
- OpenAI GPT (opcional)

## 📈 **Reportes PDF**

Los reportes incluyen:

- **Resumen Ejecutivo**: Puntos clave y recomendaciones
- **Gráficos de Rendimiento**: Tiempo de respuesta vs carga
- **Análisis de Degradación**: Puntos críticos identificados
- **Métricas Detalladas**: Throughput, percentiles, errores
- **Configuración de Prueba**: Parámetros utilizados

## 🔒 **Seguridad**

- Validación de entrada en todos los endpoints
- Sanitización de datos de usuario
- Límites de tamaño de archivo (10MB)
- Timeout en llamadas externas
- No persistencia de credenciales sensibles

## 📚 **Documentación**

- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Data Formats](docs/DATA_FORMATS.md)

## 🤝 **Contribuir**

1. Fork el repositorio
2. Crea una rama feature (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## 📄 **Licencia**

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 👨‍💻 **Autor**

**Salvador Galiano** - Desarrollo inicial

---

⭐ **¡Dale una estrella si este proyecto te ayuda!**