"""
Test Result Repository Implementation
SQLAlchemy implementation of TestResult repository interface
"""

import logging
from typing import List, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from loadtester.domain.entities.domain_entities import TestResult, ErrorDetail, PerformanceMetric
from loadtester.domain.interfaces.domain_interfaces import TestResultRepositoryInterface
from loadtester.infrastructure.database.database_models import TestResultModel, ErrorDetailModel, PerformanceMetricModel
from loadtester.shared.exceptions.infrastructure_exceptions import DatabaseError, NotFoundError

logger = logging.getLogger(__name__)


class TestResultRepository(TestResultRepositoryInterface):
    """SQLAlchemy implementation of TestResult repository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, result: TestResult) -> TestResult:
        """Create a new test result."""
        try:
            result_model = TestResultModel(
                execution_id=result.execution_id,
                avg_response_time_ms=result.avg_response_time_ms,
                p95_response_time_ms=result.p95_response_time_ms,
                p99_response_time_ms=result.p99_response_time_ms,
                min_response_time_ms=result.min_response_time_ms,
                max_response_time_ms=result.max_response_time_ms,
                total_requests=result.total_requests,
                successful_requests=result.successful_requests,
                failed_requests=result.failed_requests,
                success_rate_percent=result.success_rate_percent,
                requests_per_second=result.requests_per_second,
                actual_concurrent_users=result.actual_concurrent_users,
                actual_volumetry_used=result.actual_volumetry_used,
                data_sent_kb=result.data_sent_kb,
                data_received_kb=result.data_received_kb,
                http_errors_4xx=result.http_errors_4xx,
                http_errors_5xx=result.http_errors_5xx,
                timeout_errors=result.timeout_errors,
                connection_errors=result.connection_errors,
                error_summary=result.error_summary,
            )
            
            self.session.add(result_model)
            await self.session.commit()
            await self.session.refresh(result_model)
            
            # Create error details if any
            if result.error_details:
                for error_detail in result.error_details:
                    error_model = ErrorDetailModel(
                        result_id=result_model.result_id,
                        error_type=error_detail.error_type,
                        error_code=error_detail.error_code,
                        error_message=error_detail.error_message,
                        error_count=error_detail.error_count,
                        error_percentage=error_detail.error_percentage,
                    )
                    self.session.add(error_model)
            
            # Create performance metrics if any
            if result.performance_metrics:
                for metric in result.performance_metrics:
                    metric_model = PerformanceMetricModel(
                        result_id=result_model.result_id,
                        metric_name=metric.metric_name,
                        metric_type=metric.metric_type,
                        metric_value=metric.metric_value,
                        unit_of_measure=metric.unit_of_measure,
                        timestamp_collected=metric.timestamp_collected,
                    )
                    self.session.add(metric_model)
            
            await self.session.commit()
            
            logger.info(f"Created test result for execution: {result.execution_id}")
            
            return await self.get_by_id(result_model.result_id)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating test result: {str(e)}")
            raise DatabaseError(f"Failed to create test result: {str(e)}")
    
    async def get_by_id(self, result_id: int) -> Optional[TestResult]:
        """Get test result by ID."""
        try:
            stmt = (
                select(TestResultModel)
                .options(
                    selectinload(TestResultModel.error_details),
                    selectinload(TestResultModel.performance_metrics)
                )
                .where(TestResultModel.result_id == result_id)
            )
            
            result = await self.session.execute(stmt)
            result_model = result.scalar_one_or_none()
            
            if not result_model:
                return None
            
            return self._model_to_entity(result_model)
            
        except Exception as e:
            logger.error(f"Error getting test result by ID {result_id}: {str(e)}")
            raise DatabaseError(f"Failed to get test result: {str(e)}")
    
    async def get_by_execution_id(self, execution_id: int) -> Optional[TestResult]:
        """Get test result by execution ID."""
        try:
            stmt = (
                select(TestResultModel)
                .options(
                    selectinload(TestResultModel.error_details),
                    selectinload(TestResultModel.performance_metrics)
                )
                .where(TestResultModel.execution_id == execution_id)
            )
            
            result = await self.session.execute(stmt)
            result_model = result.scalar_one_or_none()
            
            if not result_model:
                return None
            
            return self._model_to_entity(result_model)
            
        except Exception as e:
            logger.error(f"Error getting test result for execution {execution_id}: {str(e)}")
            raise DatabaseError(f"Failed to get test result: {str(e)}")
    
    async def get_by_job_id(self, job_id: str) -> List[TestResult]:
        """Get all results for a job."""
        try:
            # This would require a complex join through executions and scenarios
            # For now, return empty list - would need to implement this relationship
            return []
            
        except Exception as e:
            logger.error(f"Error getting results for job {job_id}: {str(e)}")
            raise DatabaseError(f"Failed to get results: {str(e)}")
    
    async def update(self, result: TestResult) -> TestResult:
        """Update test result."""
        try:
            if not result.result_id:
                raise ValueError("Result ID is required for update")
            
            stmt = (
                update(TestResultModel)
                .where(TestResultModel.result_id == result.result_id)
                .values(
                    avg_response_time_ms=result.avg_response_time_ms,
                    p95_response_time_ms=result.p95_response_time_ms,
                    p99_response_time_ms=result.p99_response_time_ms,
                    min_response_time_ms=result.min_response_time_ms,
                    max_response_time_ms=result.max_response_time_ms,
                    total_requests=result.total_requests,
                    successful_requests=result.successful_requests,
                    failed_requests=result.failed_requests,
                    success_rate_percent=result.success_rate_percent,
                    requests_per_second=result.requests_per_second,
                    actual_concurrent_users=result.actual_concurrent_users,
                    actual_volumetry_used=result.actual_volumetry_used,
                    data_sent_kb=result.data_sent_kb,
                    data_received_kb=result.data_received_kb,
                    http_errors_4xx=result.http_errors_4xx,
                    http_errors_5xx=result.http_errors_5xx,
                    timeout_errors=result.timeout_errors,
                    connection_errors=result.connection_errors,
                    error_summary=result.error_summary,
                )
                .returning(TestResultModel)
            )
            
            db_result = await self.session.execute(stmt)
            updated_model = db_result.scalar_one_or_none()
            
            if not updated_model:
                raise NotFoundError(f"Test result with ID {result.result_id} not found")
            
            await self.session.commit()
            
            logger.info(f"Updated test result: {result.result_id}")
            
            return await self.get_by_id(result.result_id)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating test result {result.result_id}: {str(e)}")
            raise DatabaseError(f"Failed to update test result: {str(e)}")
    
    async def delete(self, result_id: int) -> bool:
        """Delete test result."""
        try:
            # Delete related records first
            await self.session.execute(
                delete(ErrorDetailModel).where(ErrorDetailModel.result_id == result_id)
            )
            await self.session.execute(
                delete(PerformanceMetricModel).where(PerformanceMetricModel.result_id == result_id)
            )
            
            # Delete main result
            stmt = delete(TestResultModel).where(TestResultModel.result_id == result_id)
            
            result = await self.session.execute(stmt)
            rows_affected = result.rowcount
            
            if rows_affected == 0:
                raise NotFoundError(f"Test result with ID {result_id} not found")
            
            await self.session.commit()
            
            logger.info(f"Deleted test result: {result_id}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting test result {result_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete test result: {str(e)}")
    
    def _model_to_entity(self, model: TestResultModel) -> TestResult:
        """Convert database model to domain entity."""
        # Convert error details
        error_details = []
        if hasattr(model, 'error_details') and model.error_details:
            for error_model in model.error_details:
                error_details.append(ErrorDetail(
                    error_id=error_model.error_id,
                    result_id=error_model.result_id,
                    error_type=error_model.error_type,
                    error_code=error_model.error_code,
                    error_message=error_model.error_message,
                    error_count=error_model.error_count,
                    error_percentage=error_model.error_percentage,
                ))
        
        # Convert performance metrics
        performance_metrics = []
        if hasattr(model, 'performance_metrics') and model.performance_metrics:
            for metric_model in model.performance_metrics:
                performance_metrics.append(PerformanceMetric(
                    metric_id=metric_model.metric_id,
                    result_id=metric_model.result_id,
                    metric_name=metric_model.metric_name,
                    metric_type=metric_model.metric_type,
                    metric_value=metric_model.metric_value,
                    unit_of_measure=metric_model.unit_of_measure,
                    timestamp_collected=metric_model.timestamp_collected,
                ))
        
        return TestResult(
            result_id=model.result_id,
            execution_id=model.execution_id,
            avg_response_time_ms=model.avg_response_time_ms,
            p95_response_time_ms=model.p95_response_time_ms,
            p99_response_time_ms=model.p99_response_time_ms,
            min_response_time_ms=model.min_response_time_ms,
            max_response_time_ms=model.max_response_time_ms,
            total_requests=model.total_requests,
            successful_requests=model.successful_requests,
            failed_requests=model.failed_requests,
            success_rate_percent=model.success_rate_percent,
            requests_per_second=model.requests_per_second,
            actual_concurrent_users=model.actual_concurrent_users,
            actual_volumetry_used=model.actual_volumetry_used,
            data_sent_kb=model.data_sent_kb,
            data_received_kb=model.data_received_kb,
            http_errors_4xx=model.http_errors_4xx,
            http_errors_5xx=model.http_errors_5xx,
            timeout_errors=model.timeout_errors,
            connection_errors=model.connection_errors,
            error_summary=model.error_summary,
            error_details=error_details,
            performance_metrics=performance_metrics,
        )