"""
Test Scenario Repository Implementation
SQLAlchemy implementation of TestScenario repository interface
"""

import json
import logging
from typing import List, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.test_scenario import TestScenario
from app.domain.interfaces.repositories import TestScenarioRepositoryInterface
from app.infrastructure.database.models import TestScenarioModel
from app.shared.exceptions.infrastructure import DatabaseError, NotFoundError

logger = logging.getLogger(__name__)


class TestScenarioRepository(TestScenarioRepositoryInterface):
    """SQLAlchemy implementation of TestScenario repository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, scenario: TestScenario) -> TestScenario:
        """Create a new test scenario."""
        try:
            scenario_model = TestScenarioModel(
                endpoint_id=scenario.endpoint_id,
                scenario_name=scenario.scenario_name,
                description=scenario.description,
                target_volumetry=scenario.target_volumetry,
                concurrent_users=scenario.concurrent_users,
                duration_seconds=scenario.duration_seconds,
                ramp_up_seconds=scenario.ramp_up_seconds,
                ramp_down_seconds=scenario.ramp_down_seconds,
                k6_options=json.dumps(scenario.k6_options) if scenario.k6_options else None,
                test_data=json.dumps(scenario.test_data) if scenario.test_data else None,
                created_by=scenario.created_by,
                active=scenario.active,
            )
            
            self.session.add(scenario_model)
            await self.session.commit()
            await self.session.refresh(scenario_model)
            
            logger.info(f"Created test scenario: {scenario_model.scenario_name}")
            
            return self._model_to_entity(scenario_model)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating test scenario: {str(e)}")
            raise DatabaseError(f"Failed to create test scenario: {str(e)}")
    
    async def get_by_id(self, scenario_id: int) -> Optional[TestScenario]:
        """Get test scenario by ID."""
        try:
            stmt = select(TestScenarioModel).where(TestScenarioModel.scenario_id == scenario_id)
            
            result = await self.session.execute(stmt)
            scenario_model = result.scalar_one_or_none()
            
            if not scenario_model:
                return None
            
            return self._model_to_entity(scenario_model)
            
        except Exception as e:
            logger.error(f"Error getting test scenario by ID {scenario_id}: {str(e)}")
            raise DatabaseError(f"Failed to get test scenario: {str(e)}")
    
    async def get_by_endpoint_id(self, endpoint_id: int) -> List[TestScenario]:
        """Get all scenarios for an endpoint."""
        try:
            stmt = (
                select(TestScenarioModel)
                .where(TestScenarioModel.endpoint_id == endpoint_id, TestScenarioModel.active == True)
                .order_by(TestScenarioModel.created_at.desc())
            )
            
            result = await self.session.execute(stmt)
            scenario_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in scenario_models]
            
        except Exception as e:
            logger.error(f"Error getting scenarios for endpoint {endpoint_id}: {str(e)}")
            raise DatabaseError(f"Failed to get scenarios: {str(e)}")
    
    async def get_by_job_id(self, job_id: str) -> List[TestScenario]:
        """Get all scenarios for a job."""
        try:
            # This would require a join with executions table
            # For now, return empty list - would need to implement job-scenario relationship
            return []
            
        except Exception as e:
            logger.error(f"Error getting scenarios for job {job_id}: {str(e)}")
            raise DatabaseError(f"Failed to get scenarios: {str(e)}")
    
    async def update(self, scenario: TestScenario) -> TestScenario:
        """Update test scenario."""
        try:
            if not scenario.scenario_id:
                raise ValueError("Scenario ID is required for update")
            
            stmt = (
                update(TestScenarioModel)
                .where(TestScenarioModel.scenario_id == scenario.scenario_id)
                .values(
                    scenario_name=scenario.scenario_name,
                    description=scenario.description,
                    target_volumetry=scenario.target_volumetry,
                    concurrent_users=scenario.concurrent_users,
                    duration_seconds=scenario.duration_seconds,
                    ramp_up_seconds=scenario.ramp_up_seconds,
                    ramp_down_seconds=scenario.ramp_down_seconds,
                    k6_options=json.dumps(scenario.k6_options) if scenario.k6_options else None,
                    test_data=json.dumps(scenario.test_data) if scenario.test_data else None,
                    active=scenario.active,
                )
                .returning(TestScenarioModel)
            )
            
            result = await self.session.execute(stmt)
            updated_model = result.scalar_one_or_none()
            
            if not updated_model:
                raise NotFoundError(f"Test scenario with ID {scenario.scenario_id} not found")
            
            await self.session.commit()
            
            logger.info(f"Updated test scenario: {updated_model.scenario_name}")
            
            return self._model_to_entity(updated_model)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating test scenario {scenario.scenario_id}: {str(e)}")
            raise DatabaseError(f"Failed to update test scenario: {str(e)}")
    
    async def delete(self, scenario_id: int) -> bool:
        """Delete test scenario (soft delete by setting active=False)."""
        try:
            stmt = (
                update(TestScenarioModel)
                .where(TestScenarioModel.scenario_id == scenario_id)
                .values(active=False)
                .returning(TestScenarioModel.scenario_id)
            )
            
            result = await self.session.execute(stmt)
            deleted_id = result.scalar_one_or_none()
            
            if not deleted_id:
                raise NotFoundError(f"Test scenario with ID {scenario_id} not found")
            
            await self.session.commit()
            
            logger.info(f"Deleted test scenario: {scenario_id}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting test scenario {scenario_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete test scenario: {str(e)}")
    
    def _model_to_entity(self, model: TestScenarioModel) -> TestScenario:
        """Convert database model to domain entity."""
        # Parse k6 options
        k6_options = None
        if model.k6_options:
            try:
                k6_options = json.loads(model.k6_options)
            except json.JSONDecodeError as e:
                logger.warning(f"Error parsing k6 options: {str(e)}")
        
        # Parse test data
        test_data = None
        if model.test_data:
            try:
                test_data = json.loads(model.test_data)
            except json.JSONDecodeError as e:
                logger.warning(f"Error parsing test data: {str(e)}")
        
        return TestScenario(
            scenario_id=model.scenario_id,
            endpoint_id=model.endpoint_id,
            scenario_name=model.scenario_name,
            description=model.description,
            target_volumetry=model.target_volumetry,
            concurrent_users=model.concurrent_users,
            duration_seconds=model.duration_seconds,
            ramp_up_seconds=model.ramp_up_seconds,
            ramp_down_seconds=model.ramp_down_seconds,
            k6_options=k6_options,
            test_data=test_data,
            created_at=model.created_at,
            created_by=model.created_by,
            active=model.active,
        )