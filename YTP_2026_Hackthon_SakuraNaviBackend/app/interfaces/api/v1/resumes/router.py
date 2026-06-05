"""Resumes API router."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.resume.commands import CreateResumeCommand, SetPrimaryResumeCommand, UpdateResumeCommand
from app.application.resume.service import ResumeApplicationService
from app.core.exceptions import ResourceNotFoundException
from app.interfaces.api.deps import get_current_user_id, get_resume_app_service
from app.interfaces.api.v1.resumes.schemas import (
    CreateResumeRequest,
    ResumeResponse,
    UpdateResumeRequest,
)

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post(
    "",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="建立新履歷",
    description="建立一份新的履歷。",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "未提供或無效的 Bearer Token"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"description": "欄位驗證失敗"},
    },
)
async def create_resume(
    body: CreateResumeRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[ResumeApplicationService, Depends(get_resume_app_service)],
) -> ResumeResponse:
    cmd = CreateResumeCommand(
        user_id=user_id,
        title=body.title,
        summary=body.summary,
        skills=tuple(s.model_dump() for s in body.skills) if body.skills else (),
        work_experiences=tuple(e.model_dump() for e in body.work_experiences) if body.work_experiences else (),
        external_links=tuple(l.model_dump() for l in body.external_links) if body.external_links else (),
        expected_salary=body.expected_salary.model_dump() if body.expected_salary else None,
        work_time_range=body.work_time_range.model_dump() if body.work_time_range else None,
    )
    try:
        dto = await svc.create_resume(cmd)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))
    return ResumeResponse(**dto.__dict__)


@router.get(
    "",
    response_model=list[ResumeResponse],
    summary="取得目前使用者的所有履歷",
    description="取得目前認證使用者擁有的所有履歷。",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "未提供或無效的 Bearer Token"},
    },
)
async def get_my_resumes(
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[ResumeApplicationService, Depends(get_resume_app_service)],
) -> list[ResumeResponse]:
    dtos = await svc.get_resumes(user_id)
    return [ResumeResponse(**dto.__dict__) for dto in dtos]


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    summary="取得特定履歷",
    description="取得指定履歷的詳細資料（僅限擁有者）。",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "未提供或無效的 Bearer Token"},
        status.HTTP_404_NOT_FOUND: {"description": "履歷不存在或非擁有者"},
    },
)
async def get_resume(
    resume_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[ResumeApplicationService, Depends(get_resume_app_service)],
) -> ResumeResponse:
    try:
        dto = await svc.get_resume(resume_id, user_id)
    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return ResumeResponse(**dto.__dict__)


@router.put(
    "/{resume_id}",
    response_model=ResumeResponse,
    summary="更新履歷",
    description="更新指定履歷的資料（僅限擁有者）。",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "未提供或無效的 Bearer Token"},
        status.HTTP_404_NOT_FOUND: {"description": "履歷不存在或非擁有者"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"description": "欄位驗證失敗"},
    },
)
async def update_resume(
    resume_id: str,
    body: UpdateResumeRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[ResumeApplicationService, Depends(get_resume_app_service)],
) -> ResumeResponse:
    provided = set(body.model_fields_set)

    cmd = UpdateResumeCommand(
        user_id=user_id,
        resume_id=resume_id,
        provided_fields=frozenset(provided),
        title=body.title,
        summary=body.summary,
        skills=tuple(s.model_dump() for s in body.skills) if body.skills else (),
        work_experiences=tuple(e.model_dump() for e in body.work_experiences) if body.work_experiences else (),
        external_links=tuple(l.model_dump() for l in body.external_links) if body.external_links else (),
        expected_salary=body.expected_salary.model_dump() if body.expected_salary else None,
        work_time_range=body.work_time_range.model_dump() if body.work_time_range else None,
    )
    try:
        dto = await svc.update_resume(cmd)
    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))
    return ResumeResponse(**dto.__dict__)


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="刪除履歷",
    description="刪除指定履歷（僅限擁有者）。",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "未提供或無效的 Bearer Token"},
        status.HTTP_404_NOT_FOUND: {"description": "履歷不存在或非擁有者"},
    },
)
async def delete_resume(
    resume_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[ResumeApplicationService, Depends(get_resume_app_service)],
) -> None:
    try:
        await svc.delete_resume(resume_id, user_id)
    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)


@router.patch(
    "/{resume_id}/primary",
    response_model=ResumeResponse,
    summary="設定為主要履歷",
    description="將指定履歷設定為使用者的主要履歷。",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "未提供或無效的 Bearer Token"},
        status.HTTP_404_NOT_FOUND: {"description": "履歷不存在或非擁有者"},
    },
)
async def set_primary_resume(
    resume_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[ResumeApplicationService, Depends(get_resume_app_service)],
) -> ResumeResponse:
    cmd = SetPrimaryResumeCommand(user_id=user_id, resume_id=resume_id)
    try:
        dto = await svc.set_primary(cmd)
    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return ResumeResponse(**dto.__dict__)
