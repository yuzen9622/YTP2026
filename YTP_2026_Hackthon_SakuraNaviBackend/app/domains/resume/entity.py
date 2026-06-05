"""Resume aggregate root and related entities."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.domains.resume.exceptions import ResumeNotFoundException
from app.domains.resume.value_objects import (
    ExpectedSalary,
    ExternalLink,
    ResumeCreatedAt,
    ResumeId,
    ResumeSummary,
    ResumeTitle,
    ResumeUpdatedAt,
    WorkExperience,
    WorkTimeRange,
    ResumeSkill,
    ResumeSkills,
)


@dataclass
class Resume:
    """Resume aggregate root.

    Each user can own multiple resumes for different purposes.
    Personal identity fields (name, email, phone) are read from the User entity,
    not stored here.
    """
    _id: ResumeId
    _user_id: str  # User UUID as string — immutable identity link
    _title: ResumeTitle
    _summary: Optional[ResumeSummary]
    _skills: Optional[ResumeSkills]
    _work_experiences: tuple[WorkExperience, ...]
    _external_links: tuple[ExternalLink, ...]
    _expected_salary: Optional[ExpectedSalary]
    _work_time_range: Optional[WorkTimeRange]
    _is_primary: bool
    _created_at: ResumeCreatedAt
    _updated_at: ResumeUpdatedAt

    def __init__(
        self,
        id: ResumeId,
        user_id: str,
        title: str,
        summary: Optional[str] = None,
        skills: Optional[list] = None,
        work_experiences: Optional[list] = None,
        external_links: Optional[list] = None,
        expected_salary: Optional[dict] = None,
        work_time_range: Optional[dict] = None,
        is_primary: bool = False,
        created_at: Optional[datetime] = None,
    ) -> None:
        self._id = id
        self._user_id = user_id
        self._title = ResumeTitle(title)
        self._summary = ResumeSummary(summary) if summary is not None else None
        if skills is not None:
            skill_objs = tuple(ResumeSkill(s["name"], s.get("level", "intermediate")) for s in skills)
            self._skills = ResumeSkills(skill_objs)
        else:
            self._skills = None
        if work_experiences is not None:
            self._work_experiences = tuple(
                WorkExperience(
                    company=exp["company"],
                    position=exp["position"],
                    description=exp.get("description", ""),
                    start_date=exp["start_date"],
                    end_date=exp.get("end_date", "present"),
                    is_current=exp.get("is_current", False),
                )
                for exp in work_experiences
            )
        else:
            self._work_experiences = ()
        if external_links is not None:
            self._external_links = tuple(
                ExternalLink(link["label"], link["url"])
                for link in external_links
            )
        else:
            self._external_links = ()
        if expected_salary is not None:
            self._expected_salary = ExpectedSalary(
                min=expected_salary["min"],
                max=expected_salary["max"],
                currency=expected_salary["currency"],
            )
        else:
            self._expected_salary = None
        if work_time_range is not None:
            from app.domains.resume.value_objects import WorkTimeType
            self._work_time_range = WorkTimeRange(
                start_time=work_time_range["start_time"],
                end_time=work_time_range["end_time"],
                work_time_type=WorkTimeType(work_time_range["work_time_type"]),
            )
        else:
            self._work_time_range = None
        self._is_primary = is_primary
        self._created_at = ResumeCreatedAt(created_at or datetime.now(tz=timezone.utc))
        self._updated_at = ResumeUpdatedAt(self._created_at.value)

    def id(self) -> ResumeId:
        return self._id

    def user_id(self) -> str:
        return self._user_id

    def title(self) -> str:
        return self._title.value

    def summary(self) -> Optional[str]:
        return self._summary.value if self._summary else None

    def skills(self) -> Optional[tuple[ResumeSkill, ...]]:
        return self._skills.value if self._skills else None

    def work_experiences(self) -> tuple[WorkExperience, ...]:
        return self._work_experiences

    def external_links(self) -> tuple[ExternalLink, ...]:
        return self._external_links

    def expected_salary(self) -> Optional[ExpectedSalary]:
        return self._expected_salary

    def work_time_range(self) -> Optional[WorkTimeRange]:
        return self._work_time_range

    def is_primary(self) -> bool:
        return self._is_primary

    def created_at(self) -> datetime:
        return self._created_at.value

    def updated_at(self) -> datetime:
        return self._updated_at.value

    def update_title(self, new_title: str, now: datetime) -> None:
        self._title = ResumeTitle(new_title)
        self._updated_at = ResumeUpdatedAt(now)

    def update_summary(self, new_summary: Optional[str], now: datetime) -> None:
        self._summary = ResumeSummary(new_summary) if new_summary is not None else None
        self._updated_at = ResumeUpdatedAt(now)

    def update_skills(self, new_skills: Optional[list], now: datetime) -> None:
        if new_skills is not None:
            skill_objs = tuple(ResumeSkill(s["name"], s.get("level", "intermediate")) for s in new_skills)
            self._skills = ResumeSkills(skill_objs)
        else:
            self._skills = None
        self._updated_at = ResumeUpdatedAt(now)

    def update_work_experiences(self, new_experiences: Optional[list], now: datetime) -> None:
        if new_experiences is not None:
            self._work_experiences = tuple(
                WorkExperience(
                    company=exp["company"],
                    position=exp["position"],
                    description=exp.get("description", ""),
                    start_date=exp["start_date"],
                    end_date=exp.get("end_date", "present"),
                    is_current=exp.get("is_current", False),
                )
                for exp in new_experiences
            )
        else:
            self._work_experiences = ()
        self._updated_at = ResumeUpdatedAt(now)

    def update_external_links(self, new_links: Optional[list], now: datetime) -> None:
        if new_links is not None:
            self._external_links = tuple(
                ExternalLink(link["label"], link["url"])
                for link in new_links
            )
        else:
            self._external_links = ()
        self._updated_at = ResumeUpdatedAt(now)

    def update_expected_salary(self, new_salary: Optional[dict], now: datetime) -> None:
        if new_salary is not None:
            self._expected_salary = ExpectedSalary(
                min=new_salary["min"],
                max=new_salary["max"],
                currency=new_salary["currency"],
            )
        else:
            self._expected_salary = None
        self._updated_at = ResumeUpdatedAt(now)

    def update_work_time_range(self, new_range: Optional[dict], now: datetime) -> None:
        from app.domains.resume.value_objects import WorkTimeType
        if new_range is not None:
            self._work_time_range = WorkTimeRange(
                start_time=new_range["start_time"],
                end_time=new_range["end_time"],
                work_time_type=WorkTimeType(new_range["work_time_type"]),
            )
        else:
            self._work_time_range = None
        self._updated_at = ResumeUpdatedAt(now)

    def set_primary(self, now: datetime) -> None:
        self._is_primary = True
        self._updated_at = ResumeUpdatedAt(now)

    def unset_primary(self, now: datetime) -> None:
        self._is_primary = False
        self._updated_at = ResumeUpdatedAt(now)

    @classmethod
    def _restore(
        cls,
        id: ResumeId,
        user_id: str,
        title: str,
        summary: Optional[str],
        skills: Optional[list],
        work_experiences: Optional[list],
        external_links: Optional[list],
        expected_salary: Optional[dict],
        work_time_range: Optional[dict],
        is_primary: bool,
        created_at: datetime,
        updated_at: datetime,
    ) -> "Resume":
        obj = cls.__new__(cls)
        obj._id = id
        obj._user_id = user_id
        obj._title = ResumeTitle(title)
        obj._summary = ResumeSummary(summary) if summary is not None else None
        if skills is not None:
            skill_objs = tuple(ResumeSkill(s["name"], s.get("level", "intermediate")) for s in skills)
            obj._skills = ResumeSkills(skill_objs)
        else:
            obj._skills = None
        if work_experiences is not None:
            obj._work_experiences = tuple(
                WorkExperience(
                    company=exp["company"],
                    position=exp["position"],
                    description=exp.get("description", ""),
                    start_date=exp["start_date"],
                    end_date=exp.get("end_date", "present"),
                    is_current=exp.get("is_current", False),
                )
                for exp in work_experiences
            )
        else:
            obj._work_experiences = ()
        if external_links is not None:
            obj._external_links = tuple(
                ExternalLink(link["label"], link["url"])
                for link in external_links
            )
        else:
            obj._external_links = ()
        if expected_salary is not None:
            obj._expected_salary = ExpectedSalary(
                min=expected_salary["min"],
                max=expected_salary["max"],
                currency=expected_salary["currency"],
            )
        else:
            obj._expected_salary = None
        if work_time_range is not None:
            from app.domains.resume.value_objects import WorkTimeType
            obj._work_time_range = WorkTimeRange(
                start_time=work_time_range["start_time"],
                end_time=work_time_range["end_time"],
                work_time_type=WorkTimeType(work_time_range["work_time_type"]),
            )
        else:
            obj._work_time_range = None
        obj._is_primary = is_primary
        obj._created_at = ResumeCreatedAt(created_at)
        obj._updated_at = ResumeUpdatedAt(updated_at)
        return obj
