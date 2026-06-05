"""Application service for resume-related use cases."""
import uuid
from datetime import datetime, timezone

from app.application.resume.commands import CreateResumeCommand, SetPrimaryResumeCommand, UpdateResumeCommand
from app.application.resume.dtos import ResumeDTO, ResumeWithUserDTO
from app.domains.resume.entity import Resume
from app.domains.resume.repository import ResumeRepository
from app.domains.resume.value_objects import ResumeId
from app.domains.user.repository import UserRepository
from app.core.exceptions import ResourceNotFoundException


class ResumeApplicationService:
    """Application service orchestrating resume-related use cases."""

    def __init__(
        self,
        resume_repo: ResumeRepository,
        user_repo: UserRepository,
    ) -> None:
        self._resume_repo = resume_repo
        self._user_repo = user_repo

    async def create_resume(self, cmd: CreateResumeCommand) -> ResumeDTO:
        now = datetime.now(tz=timezone.utc)
        resume = Resume(
            id=ResumeId(uuid.uuid4()),
            user_id=cmd.user_id,
            title=cmd.title,
            summary=cmd.summary,
            skills=list(cmd.skills) if cmd.skills else None,
            work_experiences=list(cmd.work_experiences) if cmd.work_experiences else None,
            external_links=list(cmd.external_links) if cmd.external_links else None,
            expected_salary=cmd.expected_salary,
            work_time_range=cmd.work_time_range,
            is_primary=False,
            created_at=now,
        )
        await self._resume_repo.save(resume)
        return self._to_dto(resume)

    async def get_resumes(self, user_id: str) -> list[ResumeDTO]:
        resumes = await self._resume_repo.find_by_user_id(user_id)
        return [self._to_dto(r) for r in resumes]

    async def get_resume(self, resume_id: str, user_id: str) -> ResumeDTO:
        resume = await self._resume_repo.find_by_id(ResumeId(uuid.UUID(resume_id)))
        if resume is None:
            raise ResourceNotFoundException(
                f"Resume '{resume_id}' not found.", code="RESUME_NOT_FOUND"
            )
        if resume.user_id() != user_id:
            raise ResourceNotFoundException(
                f"Resume '{resume_id}' not found.", code="RESUME_NOT_FOUND"
            )
        return self._to_dto(resume)

    async def update_resume(self, cmd: UpdateResumeCommand) -> ResumeDTO:
        resume = await self._resume_repo.find_by_id(ResumeId(uuid.UUID(cmd.resume_id)))
        if resume is None or resume.user_id() != cmd.user_id:
            raise ResourceNotFoundException(
                f"Resume '{cmd.resume_id}' not found.", code="RESUME_NOT_FOUND"
            )
        now = datetime.now(tz=timezone.utc)

        if "title" in cmd.provided_fields and cmd.title is not None:
            resume.update_title(cmd.title, now)

        if "summary" in cmd.provided_fields:
            resume.update_summary(cmd.summary, now)

        if "skills" in cmd.provided_fields:
            resume.update_skills(list(cmd.skills) if cmd.skills else None, now)

        if "work_experiences" in cmd.provided_fields:
            resume.update_work_experiences(list(cmd.work_experiences) if cmd.work_experiences else None, now)

        if "external_links" in cmd.provided_fields:
            resume.update_external_links(list(cmd.external_links) if cmd.external_links else None, now)

        if "expected_salary" in cmd.provided_fields:
            resume.update_expected_salary(cmd.expected_salary, now)

        if "work_time_range" in cmd.provided_fields:
            resume.update_work_time_range(cmd.work_time_range, now)

        await self._resume_repo.save(resume)
        return self._to_dto(resume)

    async def delete_resume(self, resume_id: str, user_id: str) -> None:
        resume = await self._resume_repo.find_by_id(ResumeId(uuid.UUID(resume_id)))
        if resume is None or resume.user_id() != user_id:
            raise ResourceNotFoundException(
                f"Resume '{resume_id}' not found.", code="RESUME_NOT_FOUND"
            )
        await self._resume_repo.delete(ResumeId(uuid.UUID(resume_id)), user_id)

    async def set_primary(self, cmd: SetPrimaryResumeCommand) -> ResumeDTO:
        resume = await self._resume_repo.find_by_id(ResumeId(uuid.UUID(cmd.resume_id)))
        if resume is None or resume.user_id() != cmd.user_id:
            raise ResourceNotFoundException(
                f"Resume '{cmd.resume_id}' not found.", code="RESUME_NOT_FOUND"
            )
        now = datetime.now(tz=timezone.utc)
        await self._resume_repo.set_primary(ResumeId(uuid.UUID(cmd.resume_id)), cmd.user_id)
        resume = await self._resume_repo.find_by_id(ResumeId(uuid.UUID(cmd.resume_id)))
        return self._to_dto(resume)

    @staticmethod
    def _to_dto(resume: Resume) -> ResumeDTO:
        return ResumeDTO(
            id=str(resume.id().value),
            user_id=resume.user_id(),
            title=resume.title(),
            summary=resume.summary(),
            skills=tuple(
                {"name": s.name, "level": s.level}
                for s in (resume.skills() or ())
            ),
            work_experiences=tuple(
                {
                    "company": exp.company,
                    "position": exp.position,
                    "description": exp.description,
                    "start_date": exp.start_date,
                    "end_date": exp.end_date,
                    "is_current": exp.is_current,
                }
                for exp in resume.work_experiences()
            ),
            external_links=tuple(
                {"label": link.label, "url": link.url}
                for link in resume.external_links()
            ),
            expected_salary={
                "min": resume.expected_salary().min,
                "max": resume.expected_salary().max,
                "currency": resume.expected_salary().currency,
            } if resume.expected_salary() else None,
            work_time_range={
                "start_time": resume.work_time_range().start_time,
                "end_time": resume.work_time_range().end_time,
                "work_time_type": resume.work_time_range().work_time_type.value,
            } if resume.work_time_range() else None,
            is_primary=resume.is_primary(),
            created_at=resume.created_at(),
            updated_at=resume.updated_at(),
        )
