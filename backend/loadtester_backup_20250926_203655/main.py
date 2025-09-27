"""
LoadTester Backend Main Application
FastAPI application with dependency injection and 3-layer architecture
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from loadtester.infrastructure.config.container import Container
from loadtester.infrastructure.database.connection import DatabaseManager
from loadtester.presentation.api.v1.router import api_router
from loadtester.presentation.middleware.error_handler import ErrorHandlerMiddleware
from loadtester.presentation.middleware.logging import LoggingMiddleware
from loadtester.settings import Settings
from loadtester.shared.exceptions.base import LoadTesterException
from loadtester.shared.utils.logger import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    settings = app.state.settings
    setup_logging(settings.log_level)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Initialize database
    db_manager = DatabaseManager(settings.database_url)
    await db_manager.create_tables()
    
    # Initialize container
    container = Container()
    container.config.from_pydantic(settings)
    await container.init_resources()
    app.state.container = container
    
    logger.info("Application startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    await container.shutdown_resources()


def create_app() -> FastAPI:
    """Create FastAPI application with all configurations."""
    settings = Settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Automated API Load Testing with OpenAPI Specification",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # Store settings in app state
    app.state.settings = settings
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom middleware
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(ErrorHandlerMiddleware)
    
    # Include API router
    app.include_router(
        api_router,
        prefix="/api/v1",
        tags=["LoadTester API v1"]
    )
    
    @app.exception_handler(LoadTesterException)
    async def loadtester_exception_handler(
        request: Request, 
        exc: LoadTesterException
    ) -> JSONResponse:
        """Handle custom LoadTester exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": exc.error_type,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, 
        exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        logger = logging.getLogger(__name__)
        logger.exception("Unexpected error occurred")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "internal_server_error",
                    "message": "An unexpected error occurred",
                    "details": None,
                }
            },
        )
    
    @app.get("/health")
    async def health_check() -> dict:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
        }
    
    @app.get("/")
    async def root() -> dict:
        """Root endpoint."""
        return {
            "message": f"Welcome to {settings.app_name} API",
            "version": settings.app_version,
            "docs": "/docs",
        }
    
    return app


# Create the FastAPI app instance
app = create_app()