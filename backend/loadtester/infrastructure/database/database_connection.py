"""
Database Connection Management
SQLAlchemy async database connection and session management
"""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from .database_models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection and session manager."""
    
    def __init__(self, database_url: str):
        """Initialize database manager with connection URL."""
        self.database_url = database_url
        
        # Convert sqlite:// to sqlite+aiosqlite:// for async support
        if database_url.startswith("sqlite://"):
            self.async_database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")
        else:
            self.async_database_url = database_url
        
        # Create async engine
        self.engine = create_async_engine(
            self.async_database_url,
            echo=False,  # Set to True for SQL debugging
            future=True,
            # SQLite specific settings
            poolclass=StaticPool if "sqlite" in database_url else None,
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
        )
        
        # Create session factory
        self.async_session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    async def drop_tables(self) -> None:
        """Drop all database tables (for testing)."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Error dropping database tables: {e}")
            raise
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session."""
        async with self.async_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self) -> None:
        """Close database connections."""
        try:
            await self.engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
            raise


# Global database manager instance
_db_manager: DatabaseManager = None


def init_database(database_url: str) -> None:
    """Initialize global database manager."""
    global _db_manager
    _db_manager = DatabaseManager(database_url)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    if _db_manager is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    async for session in _db_manager.get_session():
        yield session


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    if _db_manager is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db_manager