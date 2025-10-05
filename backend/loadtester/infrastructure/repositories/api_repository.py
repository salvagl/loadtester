"""
API Repository Implementation
SQLAlchemy implementation of API repository interface
"""

import logging
from typing import List, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from loadtester.domain.entities.domain_entities import API
from loadtester.domain.interfaces.domain_interfaces import APIRepositoryInterface
from loadtester.infrastructure.database.database_models import APIModel, EndpointModel
from loadtester.shared.exceptions.infrastructure_exceptions import DatabaseError, NotFoundError

logger = logging.getLogger(__name__)


class APIRepository(APIRepositoryInterface):
    """SQLAlchemy implementation of API repository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, api: API) -> API:
        """Create a new API."""
        try:
            api_model = APIModel(
                api_name=api.api_name,
                base_url=api.base_url,
                description=api.description,
                active=api.active,
            )
            
            self.session.add(api_model)
            await self.session.commit()
            await self.session.refresh(api_model)
            
            logger.info(f"Created API: {api_model.api_name} (ID: {api_model.api_id})")
            
            return self._model_to_entity(api_model)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating API: {str(e)}")
            raise DatabaseError(f"Failed to create API: {str(e)}")
    
    async def get_by_id(self, api_id: int) -> Optional[API]:
        """Get API by ID."""
        try:
            stmt = (
                select(APIModel)
                .options(selectinload(APIModel.endpoints))
                .where(APIModel.api_id == api_id)
            )
            
            result = await self.session.execute(stmt)
            api_model = result.scalar_one_or_none()
            
            if not api_model:
                return None
            
            return self._model_to_entity(api_model)
            
        except Exception as e:
            logger.error(f"Error getting API by ID {api_id}: {str(e)}")
            raise DatabaseError(f"Failed to get API: {str(e)}")
    
    async def get_by_name(self, name: str) -> Optional[API]:
        """Get API by name."""
        try:
            stmt = (
                select(APIModel)
                .options(selectinload(APIModel.endpoints))
                .where(APIModel.api_name == name)
            )
            
            result = await self.session.execute(stmt)
            api_model = result.scalar_one_or_none()
            
            if not api_model:
                return None
            
            return self._model_to_entity(api_model)
            
        except Exception as e:
            logger.error(f"Error getting API by name {name}: {str(e)}")
            raise DatabaseError(f"Failed to get API: {str(e)}")
    
    async def get_all(self) -> List[API]:
        """Get all APIs."""
        try:
            stmt = (
                select(APIModel)
                .options(selectinload(APIModel.endpoints))
                .where(APIModel.active == True)
                .order_by(APIModel.created_at.desc())
            )
            
            result = await self.session.execute(stmt)
            api_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in api_models]
            
        except Exception as e:
            logger.error(f"Error getting all APIs: {str(e)}")
            raise DatabaseError(f"Failed to get APIs: {str(e)}")
    
    async def update(self, api: API) -> API:
        """Update API."""
        try:
            if not api.api_id:
                raise ValueError("API ID is required for update")
            
            stmt = (
                update(APIModel)
                .where(APIModel.api_id == api.api_id)
                .values(
                    api_name=api.api_name,
                    base_url=api.base_url,
                    description=api.description,
                    active=api.active,
                )
                .returning(APIModel)
            )
            
            result = await self.session.execute(stmt)
            updated_model = result.scalar_one_or_none()
            
            if not updated_model:
                raise NotFoundError(f"API with ID {api.api_id} not found")
            
            await self.session.commit()
            
            logger.info(f"Updated API: {updated_model.api_name} (ID: {updated_model.api_id})")
            
            return self._model_to_entity(updated_model)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating API {api.api_id}: {str(e)}")
            raise DatabaseError(f"Failed to update API: {str(e)}")
    
    async def delete(self, api_id: int) -> bool:
        """Delete API (soft delete by setting active=False)."""
        try:
            stmt = (
                update(APIModel)
                .where(APIModel.api_id == api_id)
                .values(active=False)
                .returning(APIModel.api_id)
            )
            
            result = await self.session.execute(stmt)
            deleted_id = result.scalar_one_or_none()
            
            if not deleted_id:
                raise NotFoundError(f"API with ID {api_id} not found")
            
            await self.session.commit()
            
            logger.info(f"Deleted API: {api_id}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting API {api_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete API: {str(e)}")
    
    def _model_to_entity(self, model: APIModel) -> API:
        """Convert database model to domain entity."""
        from loadtester.infrastructure.repositories.endpoint_repository import EndpointRepository
        
        api = API(
            api_id=model.api_id,
            api_name=model.api_name,
            base_url=model.base_url,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
            active=model.active,
        )
        
        # Don't load endpoints here to avoid lazy loading issues
        # Endpoints will be loaded separately when needed
        
        return api