"""
Test Execution Repository Implementation
SQLAlchemy implementation of TestExecution repository interface
"""

import logging
from typing import List, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from loadtester.domain.entities.domain_entities import TestExecution, ExecutionStatus
from loadtester.domain.interfaces.domain_interfaces import TestExecutionRepositoryInterface
from loadtester.infrastructure.database.database_models import TestExecutionModel
from loadtester.shared.exceptions.infrastructure_exceptions import DatabaseError, NotFoundError

logger = logging.getLogger(__name__)


class TestExecutionRepository(TestExecutionRepositoryInterface):
    """SQLAlchemy implementation of TestExecution repository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, execution: TestExecution) -> TestExecution:
        """Create a new test execution."""
        try:
            execution_model = TestExecutionModel(
                scenario_id=execution.scenario_id,
                execution_name=execution.execution_name,
                start_time=execution.start_time,
                end_time=execution.end_time,
                status=execution.status.value,
                actual_duration_seconds=execution.actual_duration_seconds,
                k6_script_used=execution.k6_script_used,
                execution_logs=execution.execution_logs,
                executed_by=execution.executed_by,
            )
            
            self.session.add(execution_model)
            await self.session.commit()
            await self.session.refresh(execution_model)
            
            logger.info(f"Created test execution: {execution_model.execution_name}")
            
            return self._model_to_entity(execution_model)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating test execution: {str(e)}")
            raise DatabaseError(f"Failed to create test execution: {str(e)}")
    
    async def get_by_id(self, execution_id: int) -> Optional[TestExecution]:
        """Get test execution by ID."""
        try:
            stmt = select(TestExecutionModel).where(TestExecutionModel.execution_id == execution_id)
            
            result = await self.session.execute(stmt)
            execution_model = result.scalar_one_or_none()
            
            if not execution_model:
                return None
            
            return self._model_to_entity(execution_model)
            
        except Exception as e:
            logger.error(f"Error getting test execution by ID {execution_id}: {str(e)}")
            raise DatabaseError(f"Failed to get test execution: {str(e)}")
    
    async def get_by_scenario_id(self, scenario_id: int) -> List[TestExecution]:
        """Get all executions for a scenario."""
        try:
            stmt = (
                select(TestExecutionModel)
                .where(TestExecutionModel.scenario_id == scenario_id)
                .order_by(TestExecutionModel.start_time.desc())
            )
            
            result = await self.session.execute(stmt)
            execution_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in execution_models]
            
        except Exception as e:
            logger.error(f"Error getting executions for scenario {scenario_id}: {str(e)}")
            raise DatabaseError(f"Failed to get executions: {str(e)}")
    
    async def get_by_job_id(self, job_id: str) -> List[TestExecution]:
        """Get all executions for a job."""
        try:
            # This would require a job-execution relationship in the database
            # For now, return empty list - would need to implement this relationship
            return []
            
        except Exception as e:
            logger.error(f"Error getting executions for job {job_id}: {str(e)}")
            raise DatabaseError(f"Failed to get executions: {str(e)}")
    
    async def get_running_executions(self) -> List[TestExecution]:
        """Get all currently running executions."""
        try:
            stmt = (
                select(TestExecutionModel)
                .where(TestExecutionModel.status == ExecutionStatus.RUNNING.value)
                .order_by(TestExecutionModel.start_time.desc())
            )
            
            result = await self.session.execute(stmt)
            execution_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in execution_models]
            
        except Exception as e:
            logger.error(f"Error getting running executions: {str(e)}")
            raise DatabaseError(f"Failed to get running executions: {str(e)}")
    
    async def update(self, execution: TestExecution) -> TestExecution:
        """Update test execution."""
        try:
            if not execution.execution_id:
                raise ValueError("Execution ID is required for update")
            
            stmt = (
                update(TestExecutionModel)
                .where(TestExecutionModel.execution_id == execution.execution_id)
                .values(
                    execution_name=execution.execution_name,
                    start_time=execution.start_time,
                    end_time=execution.end_time,
                    status=execution.status.value,
                    actual_duration_seconds=execution.actual_duration_seconds,
                    k6_script_used=execution.k6_script_used,
                    execution_logs=execution.execution_logs,
                )
                .returning(TestExecutionModel)
            )
            
            result = await self.session.execute(stmt)
            updated_model = result.scalar_one_or_none()
            
            if not updated_model:
                raise NotFoundError(f"Test execution with ID {execution.execution_id} not found")
            
            await self.session.commit()
            
            logger.info(f"Updated test execution: {updated_model.execution_name}")
            
            return self._model_to_entity(updated_model)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating test execution {execution.execution_id}: {str(e)}")
            raise DatabaseError(f"Failed to update test execution: {str(e)}")
    
    async def delete(self, execution_id: int) -> bool:
        """Delete test execution."""
        try:
            stmt = delete(TestExecutionModel).where(TestExecutionModel.execution_id == execution_id)
            
            result = await self.session.execute(stmt)
            rows_affected = result.rowcount
            
            if rows_affected == 0:
                raise NotFoundError(f"Test execution with ID {execution_id} not found")
            
            await self.session.commit()
            
            logger.info(f"Deleted test execution: {execution_id}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting test execution {execution_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete test execution: {str(e)}")
    
    def _model_to_entity(self, model: TestExecutionModel) -> TestExecution:
        """Convert database model to domain entity."""
        return TestExecution(
            execution_id=model.execution_id,
            scenario_id=model.scenario_id,
            execution_name=model.execution_name,
            start_time=model.start_time,
            end_time=model.end_time,
            status=ExecutionStatus(model.status),
            actual_duration_seconds=model.actual_duration_seconds,
            k6_script_used=model.k6_script_used,
            execution_logs=model.execution_logs,
            executed_by=model.executed_by,
        )