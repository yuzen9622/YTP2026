"""Application service for guided resume draft flow."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.application.resume.commands import CreateResumeCommand
from app.application.resume.dtos import ResumeDTO
from app.application.resume.service import ResumeApplicationService
from app.application.resume_draft.commands import (
    FinalizeResumeDraftCommand,
    LoadResumeForEditCommand,
    StartResumeDraftCommand,
    UpdateResumeDraftCommand,
)
from app.application.resume_draft.dtos import ResumeDraftProgressDTO
from app.core.exceptions import ResourceNotFoundException
from app.domains.resume_draft.entity import ResumeDraft
from app.domains.resume_draft.repository import ResumeDraftRepository
from app.domains.resume_draft.value_objects import ResumeDraftId

_ALLOWED_PATCH_FIELDS: set[str] = {
    "title",
    "summary",
    "skills",
    "work_experiences",
    "external_links",
    "expected_salary",
    "work_time_range",
}


class ResumeDraftApplicationService:
    """Orchestrates resume draft state and finalize workflow."""

    def __init__(
        self,
        draft_repo: ResumeDraftRepository,
        resume_service: ResumeApplicationService,
    ) -> None:
        self._draft_repo = draft_repo
        self._resume_service = resume_service

    async def start_or_get_draft(
        self,
        cmd: StartResumeDraftCommand,
    ) -> ResumeDraftProgressDTO:
        draft = await self._draft_repo.find_active_by_user_and_conversation(
            cmd.user_id,
            cmd.conversation_id,
        )
        if draft is None:
            draft = ResumeDraft(
                id=ResumeDraftId(uuid.uuid4()),
                user_id=cmd.user_id,
                conversation_id=cmd.conversation_id,
            )
            await self._draft_repo.save(draft)
        return self._to_progress_dto(draft)

    async def load_resume_for_edit(
        self,
        cmd: LoadResumeForEditCommand,
    ) -> ResumeDraftProgressDTO:
        resume_dto = await self._resume_service.get_resume(
            cmd.resume_id, cmd.user_id
        )
        resume_data = {
            "title": resume_dto.title,
            "summary": resume_dto.summary,
            "skills": list(resume_dto.skills),
            "work_experiences": list(resume_dto.work_experiences),
            "external_links": list(resume_dto.external_links),
            "expected_salary": resume_dto.expected_salary,
            "work_time_range": resume_dto.work_time_range,
        }
        # Clean up any existing active draft in this conversation
        existing = await self._draft_repo.find_active_by_user_and_conversation(
            cmd.user_id,
            cmd.conversation_id,
        )
        if existing:
            await self._draft_repo.delete(existing.id())

        draft = ResumeDraft.from_existing_resume(
            id=ResumeDraftId(uuid.uuid4()),
            user_id=cmd.user_id,
            conversation_id=cmd.conversation_id,
            resume_data=resume_data,
        )
        await self._draft_repo.save(draft)
        dto = self._to_progress_dto(draft)
        return ResumeDraftProgressDTO(
            draft_id=dto.draft_id,
            conversation_id=dto.conversation_id,
            current_step=dto.current_step,
            status=dto.status,
            missing_fields=dto.missing_fields,
            collected=dto.collected,
            next_question=f"即將修改履歷「{resume_dto.title}」，請告訴我想修改什麼欄位或內容。",
            ready_to_finalize=dto.ready_to_finalize,
            loaded_resume_title=resume_dto.title,
        )

    async def update_draft(
        self,
        cmd: UpdateResumeDraftCommand,
    ) -> ResumeDraftProgressDTO:
        draft = await self._draft_repo.find_active_by_user_and_conversation(
            cmd.user_id,
            cmd.conversation_id,
        )
        if draft is None:
            raise ResourceNotFoundException(
                "No active resume draft found in this conversation.",
                code="RESUME_DRAFT_NOT_FOUND",
            )

        patch = self._normalize_patch(cmd.patch)
        if not patch:
            raise ValueError("Patch is empty or does not contain supported fields.")

        draft.merge_payload(patch, datetime.now(tz=timezone.utc))
        await self._draft_repo.save(draft)
        return self._to_progress_dto(draft)

    async def finalize_draft(
        self,
        cmd: FinalizeResumeDraftCommand,
    ) -> ResumeDTO:
        draft = await self._draft_repo.find_active_by_user_and_conversation(
            cmd.user_id,
            cmd.conversation_id,
        )
        if draft is None:
            raise ResourceNotFoundException(
                "No active resume draft found in this conversation.",
                code="RESUME_DRAFT_NOT_FOUND",
            )
        missing = draft.missing_required_fields()
        if missing:
            raise ValueError(f"Draft is incomplete. Missing required fields: {', '.join(missing)}")

        payload = self._normalize_payload_for_resume(draft.payload_json())
        resume = await self._resume_service.create_resume(
            CreateResumeCommand(
                user_id=cmd.user_id,
                title=str(payload.get("title") or ""),
                summary=payload.get("summary"),
                skills=tuple(payload.get("skills") or ()),
                work_experiences=tuple(payload.get("work_experiences") or ()),
                external_links=tuple(payload.get("external_links") or ()),
                expected_salary=payload.get("expected_salary"),
                work_time_range=payload.get("work_time_range"),
            )
        )

        draft.mark_completed(datetime.now(tz=timezone.utc))
        await self._draft_repo.delete(draft.id())
        return resume

    def _to_progress_dto(self, draft: ResumeDraft) -> ResumeDraftProgressDTO:
        missing = tuple(draft.missing_required_fields())
        payload = draft.payload_json()
        collected = {k: payload[k] for k in payload if k in _ALLOWED_PATCH_FIELDS}
        return ResumeDraftProgressDTO(
            draft_id=str(draft.id().value),
            conversation_id=draft.conversation_id(),
            current_step=draft.current_step().value,
            status=draft.status().value,
            missing_fields=missing,
            collected=collected,
            next_question=draft.next_question(),
            ready_to_finalize=(len(missing) == 0),
        )

    def _normalize_patch(self, patch: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(patch, dict):
            raise ValueError("patch must be a JSON object.")
        normalized: dict[str, Any] = {}
        for key, value in patch.items():
            if key not in _ALLOWED_PATCH_FIELDS:
                continue
            if key in {"title", "summary"} and value is not None and not isinstance(value, str):
                raise ValueError(f"{key} must be a string.")
            if key in {"skills", "work_experiences", "external_links"} and value is not None and not isinstance(value, list):
                raise ValueError(f"{key} must be an array.")
            if key in {"expected_salary", "work_time_range"} and value is not None and not isinstance(value, dict):
                raise ValueError(f"{key} must be an object.")
            normalized[key] = value
        return self._normalize_payload_for_resume(normalized)

    def _normalize_payload_for_resume(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        if "title" in payload:
            title = payload.get("title")
            normalized["title"] = title.strip() if isinstance(title, str) else title
        if "summary" in payload:
            summary = payload.get("summary")
            normalized["summary"] = summary.strip() if isinstance(summary, str) else summary
        if "skills" in payload:
            normalized["skills"] = self._normalize_skills(payload.get("skills"))
        if "work_experiences" in payload:
            normalized["work_experiences"] = self._normalize_work_experiences(payload.get("work_experiences"))
        if "external_links" in payload:
            normalized["external_links"] = self._normalize_external_links(payload.get("external_links"))
        if "expected_salary" in payload:
            normalized["expected_salary"] = self._normalize_expected_salary(payload.get("expected_salary"))
        if "work_time_range" in payload:
            normalized["work_time_range"] = self._normalize_work_time_range(payload.get("work_time_range"))
        return normalized

    @staticmethod
    def _normalize_skills(raw: Any) -> list[dict[str, str]] | None:
        if raw is None:
            return None
        if not isinstance(raw, list):
            return None
        normalized: list[dict[str, str]] = []
        for item in raw:
            if isinstance(item, str):
                name = item.strip()
                if not name:
                    continue
                normalized.append({"name": name, "level": "intermediate"})
                continue
            if isinstance(item, dict):
                name_raw = item.get("name") or item.get("skill") or item.get("title")
                if not isinstance(name_raw, str):
                    continue
                name = name_raw.strip()
                if not name:
                    continue
                level_raw = item.get("level")
                level = level_raw.strip() if isinstance(level_raw, str) and level_raw.strip() else "intermediate"
                normalized.append({"name": name, "level": level})
        return normalized

    @staticmethod
    def _normalize_work_experiences(raw: Any) -> list[dict[str, Any]] | None:
        if raw is None:
            return None
        if not isinstance(raw, list):
            return None
        normalized: list[dict[str, Any]] = []
        for item in raw:
            if isinstance(item, str):
                pos = item.strip()
                if not pos:
                    continue
                normalized.append(
                    {
                        "company": "待填寫",
                        "position": pos,
                        "description": "",
                        "start_date": "2024-01",
                        "end_date": "present",
                        "is_current": True,
                    }
                )
                continue
            if not isinstance(item, dict):
                continue

            company_raw = item.get("company") or item.get("organization") or item.get("org")
            position_raw = item.get("position") or item.get("title") or item.get("role")
            start_raw = item.get("start_date") or item.get("start")
            end_raw = item.get("end_date") or item.get("end") or "present"
            desc_raw = item.get("description") or item.get("achievements") or ""

            company = company_raw.strip() if isinstance(company_raw, str) and company_raw.strip() else "待填寫"
            position = position_raw.strip() if isinstance(position_raw, str) and position_raw.strip() else "未命名職務"
            start_date = start_raw.strip() if isinstance(start_raw, str) and start_raw.strip() else "2024-01"
            end_date = end_raw.strip() if isinstance(end_raw, str) and end_raw.strip() else "present"
            description = desc_raw.strip() if isinstance(desc_raw, str) else ""

            is_current_raw = item.get("is_current")
            is_current = bool(is_current_raw) if isinstance(is_current_raw, bool) else end_date.lower() in {"present", "current", "至今"}

            normalized.append(
                {
                    "company": company,
                    "position": position,
                    "description": description,
                    "start_date": start_date,
                    "end_date": end_date,
                    "is_current": is_current,
                }
            )
        return normalized

    @staticmethod
    def _normalize_external_links(raw: Any) -> list[dict[str, str]] | None:
        if raw is None:
            return None
        if not isinstance(raw, list):
            return None
        normalized: list[dict[str, str]] = []
        for item in raw:
            if isinstance(item, str):
                url = item.strip()
                if not url:
                    continue
                label = "Link"
                normalized.append({"label": label, "url": url})
                continue
            if not isinstance(item, dict):
                continue
            label_raw = item.get("label") or item.get("name") or "Link"
            url_raw = item.get("url") or item.get("href")
            if not isinstance(url_raw, str) or not url_raw.strip():
                continue
            label = label_raw.strip() if isinstance(label_raw, str) and label_raw.strip() else "Link"
            normalized.append({"label": label, "url": url_raw.strip()})
        return normalized

    @staticmethod
    def _normalize_expected_salary(raw: Any) -> dict[str, Any] | None:
        if raw is None:
            return None
        if not isinstance(raw, dict):
            return None
        min_raw = raw.get("min")
        max_raw = raw.get("max")
        currency_raw = raw.get("currency") or "TWD"
        try:
            min_val = int(min_raw)
            max_val = int(max_raw)
        except (TypeError, ValueError):
            return None
        if min_val < 0 or max_val < 0:
            return None
        if min_val > max_val:
            min_val, max_val = max_val, min_val
        currency = currency_raw.strip().upper() if isinstance(currency_raw, str) and currency_raw.strip() else "TWD"
        if len(currency) != 3:
            currency = "TWD"
        return {"min": min_val, "max": max_val, "currency": currency}

    @staticmethod
    def _normalize_work_time_range(raw: Any) -> dict[str, str] | None:
        if raw is None:
            return None
        if not isinstance(raw, dict):
            return None
        start_raw = raw.get("start_time")
        end_raw = raw.get("end_time")
        wt_type_raw = raw.get("work_time_type")
        if not all(isinstance(v, str) and v.strip() for v in (start_raw, end_raw, wt_type_raw)):
            return None
        wt_type = wt_type_raw.strip()
        if wt_type not in {"full_time", "part_time", "internship", "freelance"}:
            return None
        return {
            "start_time": start_raw.strip(),
            "end_time": end_raw.strip(),
            "work_time_type": wt_type,
        }
