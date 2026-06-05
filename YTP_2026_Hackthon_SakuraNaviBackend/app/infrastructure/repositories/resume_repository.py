"""SQLAlchemy implementation of ResumeRepository."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import update
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.resume.entity import Resume
from app.domains.resume.value_objects import ResumeId
from app.infrastructure.db.models.resume import ResumeModel


class ResumeRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, id: ResumeId) -> Optional[Resume]:
        result = await self._session.execute(
            select(ResumeModel).where(ResumeModel.id == id.value)
        )
        row = result.scalar_one_or_none()
        return self._reconstruct(row) if row else None

    async def find_by_user_id(self, user_id: str) -> list[Resume]:
        result = await self._session.execute(
            select(ResumeModel)
            .where(ResumeModel.user_id == uuid.UUID(user_id))
            .order_by(ResumeModel.is_primary.desc(), ResumeModel.created_at.desc())
        )
        rows = result.scalars().all()
        return [self._reconstruct(row) for row in rows]

    async def save(self, resume: Resume) -> None:
        row = ResumeModel(
            id=resume.id().value,
            user_id=uuid.UUID(resume.user_id()),
            title=resume.title(),
            summary=resume.summary(),
            skills=[{"name": s.name, "level": s.level} for s in resume.skills()] if resume.skills() else None,
            work_experiences=[
                {
                    "company": exp.company,
                    "position": exp.position,
                    "description": exp.description,
                    "start_date": exp.start_date,
                    "end_date": exp.end_date,
                    "is_current": exp.is_current,
                }
                for exp in resume.work_experiences()
            ] if resume.work_experiences() else None,
            external_links=[
                {"label": link.label, "url": link.url}
                for link in resume.external_links()
            ] if resume.external_links() else None,
            expected_salary_min=resume.expected_salary().min if resume.expected_salary() else None,
            expected_salary_max=resume.expected_salary().max if resume.expected_salary() else None,
            expected_salary_currency=resume.expected_salary().currency if resume.expected_salary() else None,
            work_time_range={
                "start_time": resume.work_time_range().start_time,
                "end_time": resume.work_time_range().end_time,
                "work_time_type": resume.work_time_range().work_time_type.value,
            } if resume.work_time_range() else None,
            is_primary=resume.is_primary(),
            created_at=resume.created_at(),
            updated_at=resume.updated_at(),
        )
        await self._session.merge(row)

    async def delete(self, id: ResumeId, user_id: str) -> None:
        await self._session.execute(
            update(ResumeModel)
            .where(ResumeModel.id == id.value, ResumeModel.user_id == uuid.UUID(user_id))
            .values(deleted_at=datetime.now(tz=None))
        )

    async def set_primary(self, id: ResumeId, user_id: str) -> None:
        # Unset all primaries for this user
        await self._session.execute(
            update(ResumeModel)
            .where(ResumeModel.user_id == uuid.UUID(user_id))
            .values(is_primary=False)
        )
        # Set the specified resume as primary
        await self._session.execute(
            update(ResumeModel)
            .where(ResumeModel.id == id.value, ResumeModel.user_id == uuid.UUID(user_id))
            .values(is_primary=True)
        )

    async def find_primary_by_user_id(self, user_id: str) -> Optional[Resume]:
        result = await self._session.execute(
            select(ResumeModel)
            .where(
                ResumeModel.user_id == uuid.UUID(user_id),
                ResumeModel.is_primary == True,  # noqa: E712
            )
        )
        row = result.scalar_one_or_none()
        return self._reconstruct(row) if row else None

    @staticmethod
    def _reconstruct(row: ResumeModel) -> Resume:
        expected_salary = None
        if row.expected_salary_min is not None and row.expected_salary_max is not None:
            expected_salary = {
                "min": row.expected_salary_min,
                "max": row.expected_salary_max,
                "currency": row.expected_salary_currency,
            }

        work_time_range = None
        if row.work_time_range is not None:
            work_time_range = row.work_time_range

        return Resume._restore(
            id=ResumeId(row.id),
            user_id=str(row.user_id),
            title=row.title,
            summary=row.summary,
            skills=row.skills,
            work_experiences=row.work_experiences,
            external_links=row.external_links,
            expected_salary=expected_salary,
            work_time_range=work_time_range,
            is_primary=row.is_primary,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
