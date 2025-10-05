"""
Job Repository Implementation
SQLAlchemy implementation of Job repository interface
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from loadtester.domain.entities.domain_entities import Job, JobStatus
from loadtester.domain.interfaces.domain_interfaces import JobRepositoryInterface
from loadtester.infrastructure.database.database_models import JobModel
from loadtester.shared.exceptions.infrastructure_exceptions import DatabaseError, NotFoundError

logger = logging.getLogger(__name__)


class JobRepository(JobRepositoryInterface):
    """SQLAlchemy implementation of Job repository."""

    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, job: Job) -> Job:
        """Create a new job."""
        try:
            job_model = JobModel(
                job_id=job.job_id,
                job_type=job.job_type,
                status=job.status.value,
                progress_percentage=job.progress_percentage,
                result_data=json.dumps(job.result_data) if job.result_data else None,
                error_message=job.error_message,
                callback_url=job.callback_url,
                callback_sent=job.callback_sent,
                created_at=job.created_at or datetime.utcnow(),
                started_at=job.started_at,
                finished_at=job.finished_at,
                created_by=job.created_by,
            )

            self.session.add(job_model)
            await self.session.commit()
            await self.session.refresh(job_model)

            logger.info(f"Created job: {job_model.job_type} (ID: {job_model.job_id})")

            return self._model_to_entity(job_model)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating job: {str(e)}")
            raise DatabaseError(f"Failed to create job: {str(e)}")
    
    async def get_by_id(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        try:
            stmt = select(JobModel).where(JobModel.job_id == job_id)

            result = await self.session.execute(stmt)
            job_model = result.scalar_one_or_none()

            if not job_model:
                return None

            return self._model_to_entity(job_model)

        except Exception as e:
            logger.error(f"Error getting job by ID {job_id}: {str(e)}")
            raise DatabaseError(f"Failed to get job: {str(e)}")
    
    async def get_pending_jobs(self) -> List[Job]:
        """Get all pending jobs."""
        try:
            stmt = (
                select(JobModel)
                .where(JobModel.status == JobStatus.PENDING.value)
                .order_by(JobModel.created_at.asc())
            )
            
            result = await self.session.execute(stmt)
            job_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in job_models]
            
        except Exception as e:
            logger.error(f"Error getting pending jobs: {str(e)}")
            raise DatabaseError(f"Failed to get pending jobs: {str(e)}")
    
    async def get_running_jobs(self) -> List[Job]:
        """Get all running jobs."""
        try:
            stmt = (
                select(JobModel)
                .where(JobModel.status == JobStatus.RUNNING.value)
                .order_by(JobModel.started_at.asc())
            )

            result = await self.session.execute(stmt)
            job_models = result.scalars().all()

            return [self._model_to_entity(model) for model in job_models]

        except Exception as e:
            logger.error(f"Error getting running jobs: {str(e)}")
            raise DatabaseError(f"Failed to get running jobs: {str(e)}")
    
    async def get_jobs_by_type(self, job_type: str) -> List[Job]:
        """Get jobs by type."""
        try:
            stmt = (
                select(JobModel)
                .where(JobModel.job_type == job_type)
                .order_by(JobModel.created_at.desc())
            )
            
            result = await self.session.execute(stmt)
            job_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in job_models]
            
        except Exception as e:
            logger.error(f"Error getting jobs by type {job_type}: {str(e)}")
            raise DatabaseError(f"Failed to get jobs by type: {str(e)}")
    
    async def update(self, job: Job) -> Job:
        """Update job."""
        try:
            stmt = (
                update(JobModel)
                .where(JobModel.job_id == job.job_id)
                .values(
                    status=job.status.value,
                    progress_percentage=job.progress_percentage,
                    result_data=json.dumps(job.result_data) if job.result_data else None,
                    error_message=job.error_message,
                    callback_sent=job.callback_sent,
                    started_at=job.started_at,
                    finished_at=job.finished_at,
                )
                .returning(JobModel)
            )
            
            result = await self.session.execute(stmt)
            updated_model = result.scalar_one_or_none()
            
            if not updated_model:
                raise NotFoundError(f"Job with ID {job.job_id} not found")
            
            await self.session.commit()
            
            logger.debug(f"Updated job: {updated_model.job_id} - {updated_model.status}")
            
            return self._model_to_entity(updated_model)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating job {job.job_id}: {str(e)}")
            raise DatabaseError(f"Failed to update job: {str(e)}")
    
    async def delete(self, job_id: str) -> bool:
        """Delete job."""
        try:
            stmt = delete(JobModel).where(JobModel.job_id == job_id)
            
            result = await self.session.execute(stmt)
            rows_affected = result.rowcount
            
            if rows_affected == 0:
                raise NotFoundError(f"Job with ID {job_id} not found")
            
            await self.session.commit()
            
            logger.info(f"Deleted job: {job_id}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting job {job_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete job: {str(e)}")
    
    async def cleanup_old_jobs(self, days: int = 7) -> int:
        """Clean up old completed jobs and return count of deleted jobs."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            stmt = (
                delete(JobModel)
                .where(
                    JobModel.status.in_([JobStatus.FINISHED.value, JobStatus.FAILED.value]),
                    JobModel.finished_at < cutoff_date
                )
            )
            
            result = await self.session.execute(stmt)
            deleted_count = result.rowcount
            
            await self.session.commit()
            
            logger.info(f"Cleaned up {deleted_count} old jobs older than {days} days")
            return deleted_count
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error cleaning up old jobs: {str(e)}")
            raise DatabaseError(f"Failed to cleanup old jobs: {str(e)}")
    
    async def get_jobs_for_callback(self) -> List[Job]:
        """Get finished jobs that need callback notification."""
        try:
            stmt = (
                select(JobModel)
                .where(
                    JobModel.status == JobStatus.FINISHED.value,
                    JobModel.callback_url.isnot(None),
                    JobModel.callback_sent == False
                )
                .order_by(JobModel.finished_at.asc())
            )
            
            result = await self.session.execute(stmt)
            job_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in job_models]
            
        except Exception as e:
            logger.error(f"Error getting jobs for callback: {str(e)}")
            raise DatabaseError(f"Failed to get jobs for callback: {str(e)}")
    
    async def mark_callback_sent(self, job_id: str) -> bool:
        """Mark callback as sent for a job."""
        try:
            stmt = (
                update(JobModel)
                .where(JobModel.job_id == job_id)
                .values(callback_sent=True)
                .returning(JobModel.job_id)
            )
            
            result = await self.session.execute(stmt)
            updated_id = result.scalar_one_or_none()
            
            if not updated_id:
                raise NotFoundError(f"Job with ID {job_id} not found")
            
            await self.session.commit()
            
            logger.info(f"Marked callback as sent for job: {job_id}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error marking callback sent for job {job_id}: {str(e)}")
            raise DatabaseError(f"Failed to mark callback sent: {str(e)}")
    
    def _model_to_entity(self, model: JobModel) -> Job:
        """Convert database model to domain entity."""
        return Job(
            job_id=model.job_id,
            job_type=model.job_type,
            status=JobStatus(model.status),
            progress_percentage=model.progress_percentage,
            result_data=json.loads(model.result_data) if model.result_data else None,
            error_message=model.error_message,
            callback_url=model.callback_url,
            callback_sent=model.callback_sent,
            created_at=model.created_at,
            started_at=model.started_at,
            finished_at=model.finished_at,
            created_by=model.created_by,
        )