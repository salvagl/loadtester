# LoadTester - Estructura del Proyecto

```
loadtester/
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
├── README.md
├── .env
├── .gitignore
│
├── frontend/
│   ├── Dockerfile
│   ├── app.py
│   ├── requirements.txt
│   └── components/
│       ├── __init__.py
│       ├── openapi_parser.py
│       ├── endpoint_selector.py
│       ├── test_configurator.py
│       └── results_viewer.py
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── settings.py
│   │   │
│   │   ├── presentation/          # Capa de Presentación
│   │   │   ├── __init__.py
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── v1/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── endpoints/
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   ├── load_test.py
│   │   │   │   │   │   ├── status.py
│   │   │   │   │   │   ├── report.py
│   │   │   │   │   │   └── openapi.py
│   │   │   │   │   └── router.py
│   │   │   │   └── dependencies.py
│   │   │   └── middleware/
│   │   │       ├── __init__.py
│   │   │       ├── error_handler.py
│   │   │       └── logging.py
│   │   │
│   │   ├── domain/               # Capa de Negocio
│   │   │   ├── __init__.py
│   │   │   ├── entities/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── api.py
│   │   │   │   ├── endpoint.py
│   │   │   │   ├── test_scenario.py
│   │   │   │   ├── test_execution.py
│   │   │   │   └── test_result.py
│   │   │   ├── interfaces/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── repositories.py
│   │   │   │   ├── ai_services.py
│   │   │   │   ├── k6_service.py
│   │   │   │   └── pdf_service.py
│   │   │   └── services/
│   │   │       ├── __init__.py
│   │   │       ├── load_test_service.py
│   │   │       ├── openapi_parser_service.py
│   │   │       ├── data_mock_service.py
│   │   │       ├── k6_generator_service.py
│   │   │       └── report_service.py
│   │   │
│   │   ├── infrastructure/        # Capa de Acceso a Datos
│   │   │   ├── __init__.py
│   │   │   ├── database/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── connection.py
│   │   │   │   ├── models.py
│   │   │   │   └── migrations/
│   │   │   │       └── __init__.py
│   │   │   ├── repositories/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── api_repository.py
│   │   │   │   ├── endpoint_repository.py
│   │   │   │   ├── test_scenario_repository.py
│   │   │   │   ├── test_execution_repository.py
│   │   │   │   └── test_result_repository.py
│   │   │   ├── external/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ai_client.py
│   │   │   │   ├── k6_runner.py
│   │   │   │   └── pdf_generator.py
│   │   │   └── config/
│   │   │       ├── __init__.py
│   │   │       ├── container.py
│   │   │       └── dependencies.py
│   │   │
│   │   ├── shared/
│   │   │   ├── __init__.py
│   │   │   ├── exceptions/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── domain.py
│   │   │   │   └── infrastructure.py
│   │   │   ├── utils/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── logger.py
│   │   │   │   ├── validators.py
│   │   │   │   └── helpers.py
│   │   │   └── constants/
│   │   │       ├── __init__.py
│   │   │       └── enums.py
│   │   │
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── unit/
│   │       ├── integration/
│   │       └── conftest.py
│
├── k6/
│   ├── Dockerfile
│   ├── scripts/
│   │   └── generated/      # Scripts K6 generados dinámicamente
│   └── results/
│       └── generated/      # Resultados de K6
│
├── shared/
│   ├── data/
│   │   ├── uploads/        # Archivos de datos subidos
│   │   └── mocked/         # Datos generados automáticamente
│   ├── reports/
│   │   └── generated/      # PDFs generados
│   └── database/
│       └── loadtester.db   # SQLite database (persistente)
│
└── docs/
    ├── README.md
    ├── API.md
    ├── DEPLOYMENT.md
    └── DATA_FORMATS.md
```

## 📋 **Descripción de Componentes**

### **Frontend (Streamlit)**
- **Interfaz minimalista** para configuración de pruebas
- **Carga de OpenAPI** (URL o texto)
- **Selección de endpoints** y configuración
- **Visualización de resultados**

### **Backend (FastAPI)**
- **Arquitectura en 3 capas** desacoplada
- **Inyección de dependencias** con interfaces
- **API asíncrona** para long-jobs
- **Integración con servicios IA**

### **Base de Datos (SQLite)**
- **Persistencia** con volumen Docker
- **Modelos** siguiendo el diagrama ER especificado
- **Migraciones** automáticas

### **K6 Service**
- **Contenedor separado** para ejecución
- **Scripts generados** dinámicamente
- **Resultados** persistentes

### **Servicios Compartidos**
- **Datos uploads/mocked**
- **Reportes PDF**
- **Database persistente**