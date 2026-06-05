"""ResumeDraft aggregate root."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.domains.resume_draft.value_objects import (
    ResumeDraftId,
    ResumeDraftStatus,
    ResumeDraftStep,
)

_REQUIRED_FIELD_ORDER: tuple[str, ...] = (
    "title",
    "summary",
    "skills",
    "work_experiences",
)

_NEXT_QUESTION_BY_FIELD: dict[str, str] = {
    "title": "請提供這份履歷的標題（例如：應屆後端工程師履歷）。",
    "summary": "請提供 2-4 句履歷摘要（你的背景、強項與求職方向）。",
    "skills": "請列出你的技能（陣列格式，每筆至少含 name，可含 level）。",
    "work_experiences": "請提供至少一段工作或專案經驗（company、position、start_date 等）。",
}


@dataclass
class ResumeDraft:
    """Draft aggregate for guided resume writing in chat."""

    _id: ResumeDraftId
    _user_id: str
    _conversation_id: str
    _payload_json: dict[str, Any]
    _current_step: ResumeDraftStep
    _status: ResumeDraftStatus
    _created_at: datetime
    _updated_at: datetime

    def __init__(
        self,
        *,
        id: ResumeDraftId,
        user_id: str,
        conversation_id: str,
        payload_json: dict[str, Any] | None = None,
        current_step: ResumeDraftStep = ResumeDraftStep.TITLE,
        status: ResumeDraftStatus = ResumeDraftStatus.ACTIVE,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        self._id = id
        self._user_id = user_id
        self._conversation_id = conversation_id
        self._payload_json = dict(payload_json or {})
        self._current_step = current_step
        self._status = status
        now = datetime.now(tz=timezone.utc)
        self._created_at = created_at or now
        self._updated_at = updated_at or self._created_at
        self._refresh_step()

    def id(self) -> ResumeDraftId:
        return self._id

    def user_id(self) -> str:
        return self._user_id

    def conversation_id(self) -> str:
        return self._conversation_id

    def payload_json(self) -> dict[str, Any]:
        return dict(self._payload_json)

    def current_step(self) -> ResumeDraftStep:
        return self._current_step

    def status(self) -> ResumeDraftStatus:
        return self._status

    def created_at(self) -> datetime:
        return self._created_at

    def updated_at(self) -> datetime:
        return self._updated_at

    def missing_required_fields(self) -> list[str]:
        missing: list[str] = []
        for field in _REQUIRED_FIELD_ORDER:
            value = self._payload_json.get(field)
            if _is_missing(value):
                missing.append(field)
        return missing

    def next_question(self) -> str | None:
        missing = self.missing_required_fields()
        if missing:
            return _NEXT_QUESTION_BY_FIELD.get(missing[0])
        return "必填欄位已完成。是否要我現在幫你產生正式履歷？"

    def is_ready_to_finalize(self) -> bool:
        return len(self.missing_required_fields()) == 0

    def merge_payload(self, patch: dict[str, Any], now: datetime) -> None:
        for key, value in patch.items():
            self._payload_json[key] = value
        self._updated_at = now
        self._refresh_step()

    def mark_completed(self, now: datetime) -> None:
        self._status = ResumeDraftStatus.COMPLETED
        self._updated_at = now

    def cancel(self, now: datetime) -> None:
        self._status = ResumeDraftStatus.CANCELLED
        self._updated_at = now

    def _refresh_step(self) -> None:
        if self._status != ResumeDraftStatus.ACTIVE:
            self._current_step = ResumeDraftStep.READY_TO_FINALIZE
            return
        missing = self.missing_required_fields()
        if not missing:
            self._current_step = ResumeDraftStep.READY_TO_FINALIZE
            return
        self._current_step = ResumeDraftStep(missing[0])

    @classmethod
    def from_existing_resume(
        cls,
        *,
        id: ResumeDraftId,
        user_id: str,
        conversation_id: str,
        resume_data: dict[str, Any],
    ) -> "ResumeDraft":
        """Create a draft initialized with data from an existing resume for editing."""
        now = datetime.now(tz=timezone.utc)
        payload: dict[str, Any] = {}
        if "title" in resume_data:
            payload["title"] = resume_data["title"]
        if "summary" in resume_data:
            payload["summary"] = resume_data["summary"]
        if "skills" in resume_data:
            payload["skills"] = resume_data["skills"]
        if "work_experiences" in resume_data:
            payload["work_experiences"] = resume_data["work_experiences"]
        if "external_links" in resume_data:
            payload["external_links"] = resume_data["external_links"]
        if "expected_salary" in resume_data:
            payload["expected_salary"] = resume_data["expected_salary"]
        if "work_time_range" in resume_data:
            payload["work_time_range"] = resume_data["work_time_range"]

        obj = cls.__new__(cls)
        obj._id = id
        obj._user_id = user_id
        obj._conversation_id = conversation_id
        obj._payload_json = payload
        obj._status = ResumeDraftStatus.ACTIVE
        obj._created_at = now
        obj._updated_at = now
        obj._refresh_step()
        return obj

    @classmethod
    def _restore(
        cls,
        *,
        id: ResumeDraftId,
        user_id: str,
        conversation_id: str,
        payload_json: dict[str, Any],
        current_step: str,
        status: str,
        created_at: datetime,
        updated_at: datetime,
    ) -> "ResumeDraft":
        obj = cls.__new__(cls)
        obj._id = id
        obj._user_id = user_id
        obj._conversation_id = conversation_id
        obj._payload_json = dict(payload_json or {})
        obj._current_step = ResumeDraftStep(current_step)
        obj._status = ResumeDraftStatus(status)
        obj._created_at = created_at
        obj._updated_at = updated_at
        obj._refresh_step()
        return obj


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return len(value.strip()) == 0
    if isinstance(value, list):
        return len(value) == 0
    return False
