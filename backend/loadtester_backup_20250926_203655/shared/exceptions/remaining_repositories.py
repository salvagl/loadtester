"""
Endpoint Repository Implementation
SQLAlchemy implementation of Endpoint repository interface
"""

import json
import logging
from typing import List, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.test_scenario import Endpoint, AuthConfig, AuthType
from app.domain.interfaces.repositories import EndpointRepositoryInterface
from app.infrastructure.database.models import EndpointModel
from app.shared.exceptions.infrastructure import DatabaseError, NotFoundError

logger = logging.getLogger(__name__)


class EndpointRepository(EndpointRepositoryInterface):
    """SQLAlchemy implementation of Endpoint repository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, endpoint: Endpoint) -> Endpoint:
        """Create a new endpoint."""
        try:
            endpoint_model = EndpointModel(
                api_id=endpoint.api_id,
                endpoint_name=endpoint.endpoint_name,
                http_method=endpoint.http_method,
                endpoint_path=endpoint.endpoint_path,
                description=endpoint.description,
                expected_volumetry=endpoint.expected_volumetry,
                expected_concurrent_users=endpoint.expected_concurrent_users,
                auth_type=endpoint.auth_config.auth_type.value if endpoint.auth_config else None,
                auth_config=json.dumps(self._auth_config_to_dict(endpoint.auth_config)) if endpoint.auth_config else None,
                headers_config=json.dumps(endpoint.headers_config) if endpoint.headers_config else None,
                payload_template=json.dumps(endpoint.payload_template) if endpoint.payload_template else None,
                timeout_ms=endpoint.timeout_ms,
                active=endpoint.active,
            )
            
            self.session.add(endpoint_model)
            await self.session.commit()
            await self.session.refresh(endpoint_model)
            
            logger.info(f"Created endpoint: {endpoint_model.http_method} {endpoint_model.endpoint_path}")
            
            return self._model_to_entity(endpoint_model)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating endpoint: {str(e)}")
            raise DatabaseError(f"Failed to create endpoint: {str(e)}")
    
    async def get_by_id(self, endpoint_id: int) -> Optional[Endpoint]:
        """Get endpoint by ID."""
        try:
            stmt = select(EndpointModel).where(EndpointModel.endpoint_id == endpoint_id)
            
            result = await self.session.execute(stmt)
            endpoint_model = result.scalar_one_or_none()
            
            if not endpoint_model:
                return None
            
            return self._model_to_entity(endpoint_model)
            
        except Exception as e:
            logger.error(f"Error getting endpoint by ID {endpoint_id}: {str(e)}")
            raise DatabaseError(f"Failed to get endpoint: {str(e)}")
    
    async def get_by_api_id(self, api_id: int) -> List[Endpoint]:
        """Get all endpoints for an API."""
        try:
            stmt = (
                select(EndpointModel)
                .where(EndpointModel.api_id == api_id, EndpointModel.active == True)
                .order_by(EndpointModel.endpoint_path, EndpointModel.http_method)
            )
            
            result = await self.session.execute(stmt)
            endpoint_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in endpoint_models]
            
        except Exception as e:
            logger.error(f"Error getting endpoints for API {api_id}: {str(e)}")
            raise DatabaseError(f"Failed to get endpoints: {str(e)}")
    
    async def get_by_path_and_method(self, path: str, method: str) -> Optional[Endpoint]:
        """Get endpoint by path and HTTP method."""
        try:
            stmt = (
                select(EndpointModel)
                .where(
                    EndpointModel.endpoint_path == path,
                    EndpointModel.http_method == method.upper(),
                    EndpointModel.active == True
                )
            )
            
            result = await self.session.execute(stmt)
            endpoint_model = result.scalar_one_or_none()
            
            if not endpoint_model:
                return None
            
            return self._model_to_entity(endpoint_model)
            
        except Exception as e:
            logger.error(f"Error getting endpoint {method} {path}: {str(e)}")
            raise DatabaseError(f"Failed to get endpoint: {str(e)}")
    
    async def update(self, endpoint: Endpoint) -> Endpoint:
        """Update endpoint."""
        try:
            if not endpoint.endpoint_id:
                raise ValueError("Endpoint ID is required for update")
            
            stmt = (
                update(EndpointModel)
                .where(EndpointModel.endpoint_id == endpoint.endpoint_id)
                .values(
                    endpoint_name=endpoint.endpoint_name,
                    http_method=endpoint.http_method,
                    endpoint_path=endpoint.endpoint_path,
                    description=endpoint.description,
                    expected_volumetry=endpoint.expected_volumetry,
                    expected_concurrent_users=endpoint.expected_concurrent_users,
                    auth_type=endpoint.auth_config.auth_type.value if endpoint.auth_config else None,
                    auth_config=json.dumps(self._auth_config_to_dict(endpoint.auth_config)) if endpoint.auth_config else None,
                    headers_config=json.dumps(endpoint.headers_config) if endpoint.headers_config else None,
                    payload_template=json.dumps(endpoint.payload_template) if endpoint.payload_template else None,
                    timeout_ms=endpoint.timeout_ms,
                    active=endpoint.active,
                )
                .returning(EndpointModel)
            )
            
            result = await self.session.execute(stmt)
            updated_model = result.scalar_one_or_none()
            
            if not updated_model:
                raise NotFoundError(f"Endpoint with ID {endpoint.endpoint_id} not found")
            
            await self.session.commit()
            
            logger.info(f"Updated endpoint: {updated_model.http_method} {updated_model.endpoint_path}")
            
            return self._model_to_entity(updated_model)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating endpoint {endpoint.endpoint_id}: {str(e)}")
            raise DatabaseError(f"Failed to update endpoint: {str(e)}")
    
    async def delete(self, endpoint_id: int) -> bool:
        """Delete endpoint (soft delete by setting active=False)."""
        try:
            stmt = (
                update(EndpointModel)
                .where(EndpointModel.endpoint_id == endpoint_id)
                .values(active=False)
                .returning(EndpointModel.endpoint_id)
            )
            
            result = await self.session.execute(stmt)
            deleted_id = result.scalar_one_or_none()
            
            if not deleted_id:
                raise NotFoundError(f"Endpoint with ID {endpoint_id} not found")
            
            await self.session.commit()
            
            logger.info(f"Deleted endpoint: {endpoint_id}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting endpoint {endpoint_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete endpoint: {str(e)}")
    
    def _model_to_entity(self, model: EndpointModel) -> Endpoint:
        """Convert database model to domain entity."""
        # Parse auth config
        auth_config = None
        if model.auth_config:
            try:
                auth_data = json.loads(model.auth_config)
                auth_config = AuthConfig(
                    auth_type=AuthType(auth_data.get("auth_type", "none")),
                    token=auth_data.get("token"),
                    api_key=auth_data.get("api_key"),
                    header_name=auth_data.get("header_name"),
                    query_param_name=auth_data.get("query_param_name"),
                )
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Error parsing auth config: {str(e)}")
        
        # Parse headers config
        headers_config = None
        if model.headers_config:
            try:
                headers_config = json.loads(model.headers_config)
            except json.JSONDecodeError as e:
                logger.warning(f"Error parsing headers config: {str(e)}")
        
        # Parse payload template
        payload_template = None
        if model.payload_template:
            try:
                payload_template = json.loads(model.payload_template)
            except json.JSONDecodeError as e:
                logger.warning(f"Error parsing payload template: {str(e)}")
        
        return Endpoint(
            endpoint_id=model.endpoint_id,
            api_id=model.api_id,
            endpoint_name=model.endpoint_name,
            http_method=model.http_method,
            endpoint_path=model.endpoint_path,
            description=model.description,
            expected_volumetry=model.expected_volumetry,
            expected_concurrent_users=model.expected_concurrent_users,
            auth_config=auth_config,
            headers_config=headers_config,
            payload_template=payload_template,
            timeout_ms=model.timeout_ms,
            created_at=model.created_at,
            updated_at=model.updated_at,
            active=model.active,
        )
    
    def _auth_config_to_dict(self, auth_config: Optional[AuthConfig]) -> Optional[dict]:
        """Convert auth config entity to dictionary."""
        if not auth_config:
            return None
        
        return {
            "auth_type": auth_config.auth_type.value,
            "token": auth_config.token,
            "api_key": auth_config.api_key,
            "header_name": auth_config.header_name,
            "query_param_name": auth_config.query_param_name,
        }