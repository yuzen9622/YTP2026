"""Admin API router — admin management and user info endpoints."""
from typing import Annotated, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.admin.commands import (
    RegisterAdminCommand,
    RemoveAdminCommand,
    UpdateAdminCommand,
)
from app.application.admin.service import AdminApplicationService
from app.application.user.commands import AdminUpdateUserCommand, ListAllUsersQuery
from app.application.user.service import UserApplicationService
from app.core.exceptions import ResourceNotFoundException
from app.domains.admin.exceptions import AdminAlreadyExistsException, AdminNotFoundException
from app.domains.admin.value_objects import AdminRole
from app.interfaces.api.deps import get_admin_app_service, get_current_admin, get_user_app_service
from app.interfaces.api.v1.admin.schemas import (
    AdminListResponse,
    AdminResponse,
    CreateAdminRequest,
    UpdateAdminRequest,
)
from app.interfaces.api.v1.users.schemas import (
    AdminUpdateUserRequest,
    AdminUserListResponse,
    UserProfileResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_superadmin(role: str) -> None:
    if role != AdminRole.SUPERADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmin can perform this action.",
        )


# ── Admin management ────────────────────────────────────────────────────────────


@router.post(
    "/admins",
    response_model=AdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="新增管理者（superadmin 專用）",
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "非 superadmin"},
        status.HTTP_409_CONFLICT: {"description": "該帳號已是管理者"},
    },
)
async def create_admin(
    body: CreateAdminRequest,
    admin_info: Annotated[Tuple[str, str], Depends(get_current_admin)],
    admin_svc: Annotated[AdminApplicationService, Depends(get_admin_app_service)],
) -> AdminResponse:
    _, role = admin_info
    _require_superadmin(role)
    try:
        cmd = RegisterAdminCommand(account=body.account, password=body.password, role=body.role)
        dto = await admin_svc.register_admin(cmd)
    except AdminAlreadyExistsException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return AdminResponse(**dto.__dict__)


@router.get(
    "/admins",
    response_model=AdminListResponse,
    summary="列出所有管理者",
    responses={status.HTTP_403_FORBIDDEN: {"description": "非管理者"}},
)
async def list_admins(
    admin_info: Annotated[Tuple[str, str], Depends(get_current_admin)],
    admin_svc: Annotated[AdminApplicationService, Depends(get_admin_app_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AdminListResponse:
    result = await admin_svc.list_admins(limit=limit, offset=offset)
    return AdminListResponse(
        items=[AdminResponse(**a.__dict__) for a in result.items],
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


@router.get(
    "/admins/me",
    response_model=AdminResponse,
    summary="取得目前管理者身份",
    responses={status.HTTP_403_FORBIDDEN: {"description": "非管理者"}},
)
async def get_my_admin_status(
    admin_info: Annotated[Tuple[str, str], Depends(get_current_admin)],
    admin_svc: Annotated[AdminApplicationService, Depends(get_admin_app_service)],
) -> AdminResponse:
    admin_id, _ = admin_info
    dto = await admin_svc.get_admin_by_id(admin_id)
    return AdminResponse(**dto.__dict__)


@router.patch(
    "/admins/{admin_id}",
    response_model=AdminResponse,
    summary="變更管理者職位/狀態/密碼（superadmin 專用）",
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "非 superadmin"},
        status.HTTP_404_NOT_FOUND: {"description": "管理者不存在"},
    },
)
async def update_admin(
    admin_id: str,
    body: UpdateAdminRequest,
    admin_info: Annotated[Tuple[str, str], Depends(get_current_admin)],
    admin_svc: Annotated[AdminApplicationService, Depends(get_admin_app_service)],
) -> AdminResponse:
    _, role = admin_info
    _require_superadmin(role)
    try:
        cmd = UpdateAdminCommand(
            admin_id=admin_id,
            role=body.role,
            is_active=body.is_active,
            new_password=body.new_password,
        )
        dto = await admin_svc.update_admin(cmd)
    except AdminNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return AdminResponse(**dto.__dict__)


@router.delete(
    "/admins/{admin_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="移除管理者身份（superadmin 專用）",
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "非 superadmin"},
        status.HTTP_404_NOT_FOUND: {"description": "管理者不存在"},
    },
)
async def remove_admin(
    admin_id: str,
    admin_info: Annotated[Tuple[str, str], Depends(get_current_admin)],
    admin_svc: Annotated[AdminApplicationService, Depends(get_admin_app_service)],
) -> None:
    _, role = admin_info
    _require_superadmin(role)
    try:
        await admin_svc.remove_admin(RemoveAdminCommand(admin_id=admin_id))
    except AdminNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# ── User info (admin) ─────────────────────────────────────────────────────────


@router.get(
    "/users",
    response_model=AdminUserListResponse,
    summary="列出所有使用者（管理者專用）",
    responses={status.HTTP_403_FORBIDDEN: {"description": "非管理者"}},
)
async def list_users(
    admin_info: Annotated[Tuple[str, str], Depends(get_current_admin)],
    user_svc: Annotated[UserApplicationService, Depends(get_user_app_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: Annotated[str | None, Query(max_length=100)] = None,
    is_active: Annotated[bool | None, Query()] = None,
) -> AdminUserListResponse:
    query = ListAllUsersQuery(limit=limit, offset=offset, search=search, is_active=is_active)
    result = await user_svc.admin_list_users(query)
    return AdminUserListResponse(
        items=[UserProfileResponse(**u.__dict__) for u in result.items],
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


@router.get(
    "/users/{user_id}",
    response_model=UserProfileResponse,
    summary="取得特定使用者資料（管理者專用）",
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "非管理者"},
        status.HTTP_404_NOT_FOUND: {"description": "使用者不存在"},
    },
)
async def get_user(
    user_id: str,
    admin_info: Annotated[Tuple[str, str], Depends(get_current_admin)],
    user_svc: Annotated[UserApplicationService, Depends(get_user_app_service)],
) -> UserProfileResponse:
    try:
        dto = await user_svc.admin_get_user(user_id)
    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return UserProfileResponse(**dto.__dict__)


@router.patch(
    "/users/{user_id}",
    response_model=UserProfileResponse,
    summary="編輯指定使用者資料（管理者專用）",
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "非管理者"},
        status.HTTP_404_NOT_FOUND: {"description": "使用者不存在"},
        status.HTTP_409_CONFLICT: {"description": "欄位衝突"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"description": "資料格式錯誤"},
    },
)
async def update_user(
    user_id: str,
    body: AdminUpdateUserRequest,
    admin_info: Annotated[Tuple[str, str], Depends(get_current_admin)],
    user_svc: Annotated[UserApplicationService, Depends(get_user_app_service)],
) -> UserProfileResponse:
    admin_id, _ = admin_info
    provided = set(body.model_fields_set)
    if "tags" in provided and body.tags is None:
        provided.discard("tags")
    if "language_skills" in provided and body.language_skills is None:
        provided.discard("language_skills")

    cmd = AdminUpdateUserCommand(
        user_id=user_id,
        admin_id=admin_id,
        provided_fields=frozenset(provided),
        name=body.name,
        bio=body.bio,
        email=body.email,
        phone=body.phone,
        birth_date=body.birth_date,
        career=body.career,
        tags=tuple(body.tags) if body.tags is not None else (),
        avatar_url=body.avatar_url,
        language_skills=tuple(
            s.model_dump() for s in body.language_skills
        ) if body.language_skills is not None else (),
        registered_address=body.registered_address,
        residential_address=body.residential_address,
        is_residential_same_as_registered=body.is_residential_same_as_registered,
        gender=body.gender,
        is_active=body.is_active,
        role=body.role,
        password=body.password,
    )
    try:
        dto = await user_svc.admin_update_user(cmd)
    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))
    return UserProfileResponse(**dto.__dict__)