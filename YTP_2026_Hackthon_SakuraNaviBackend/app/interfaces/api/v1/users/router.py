"""Users API router — profile endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.application.user.commands import ChangePasswordCommand
from app.application.user.queries import GetUserProfileQuery
from app.application.user.service import UserApplicationService
from app.core.exceptions import DuplicateResourceException, ResourceNotFoundException, UnauthorizedException
from app.interfaces.api.deps import get_current_user_id, get_user_app_service
from app.interfaces.api.v1.users.schemas import (
    ChangePasswordRequest,
    UpdateProfileRequest,
    UserProfileResponse,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="取得目前使用者個人資料",
    description=(
        "回傳目前已認證使用者的個人資料。\n\n"
        "**認證方式**：在 Request Header 中帶入 `Authorization: Bearer <access_token>`。\n\n"
        "**回傳欄位**：`id`、`name`、`account`、`email`、`phone`、`bio`、"
        "`birth_date`、`career`、`tags`、`avatar_url`、`language_skills`、"
        "`registered_address`、`residential_address`、`is_residential_same_as_registered`、"
        "`is_active`、`created_at`、`updated_at`"
    ),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "未認證或 Token 無效／已過期",
            "content": {
                "application/json": {
                    "example": {"detail": "未認證或 Token 已過期", "code": "UNAUTHORIZED"}
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "使用者不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "User not found", "code": "NOT_FOUND"}
                }
            },
        },
    },
)
async def get_my_profile(
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[UserApplicationService, Depends(get_user_app_service)],
) -> UserProfileResponse:
    try:
        dto = await svc.get_profile(GetUserProfileQuery(user_id=user_id))
    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return UserProfileResponse(**dto.__dict__)


@router.patch(
    "/me",
    response_model=UserProfileResponse,
    summary="更新目前使用者個人資料",
    description=(
        "以 PATCH 方式更新目前認證使用者的個人資料。\n\n"
        "**僅需傳入要修改的欄位**，未帶入的欄位保持不變。\n\n"
        "**可清除欄位**：`email`、`phone`、`birth_date`、`career`、`avatar_url`、`registered_address`、`residential_address` 傳 `null` 即可清除；"
        "`tags` 傳空陣列 `[]` 可清除所有標籤；`language_skills` 傳空陣列可清除所有語言能力。\n\n"
        "**認證方式**：`Authorization: Bearer <access_token>`"
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "欄位驗證失敗",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "未認證或 Token 無效／已過期",
            "content": {
                "application/json": {
                    "example": {"detail": "未認證或 Token 已過期", "code": "UNAUTHORIZED"}
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Email 或手機號碼已被其他帳號使用",
            "content": {
                "application/json": {
                    "example": {"detail": "Email already registered", "code": "EMAIL_TAKEN"}
                }
            },
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "輸入資料格式不正確",
            "content": {
                "application/json": {
                    "example": {"detail": "電話格式不合法"}
                }
            },
        },
    },
)
async def update_my_profile(
    body: UpdateProfileRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[UserApplicationService, Depends(get_user_app_service)],
) -> UserProfileResponse:
    from app.application.user.commands import UpdateProfileCommand

    provided = set(body.model_fields_set)
    if "tags" in provided and body.tags is None:
        provided.discard("tags")
    if "language_skills" in provided and body.language_skills is None:
        provided.discard("language_skills")

    cmd = UpdateProfileCommand(
        user_id=user_id,
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
    )
    try:
        dto = await svc.update_profile(cmd)
    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except DuplicateResourceException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        )
    return UserProfileResponse(**dto.__dict__)


@router.put(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="修改目前使用者密碼",
    description=(
        "驗證目前密碼後，將密碼更新為新的密碼。\n\n"
        "**認證方式**：`Authorization: Bearer <access_token>`\n\n"
        "成功時回傳 `204 No Content`。"
    ),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "目前密碼不正確或 Token 無效",
            "content": {
                "application/json": {
                    "example": {"detail": "目前密碼不正確", "code": "INVALID_CREDENTIALS"}
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "使用者不存在",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "新密碼格式不符規則",
        },
    },
)
async def change_my_password(
    body: ChangePasswordRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[UserApplicationService, Depends(get_user_app_service)],
) -> Response:
    cmd = ChangePasswordCommand(
        user_id=user_id,
        current_password=body.current_password,
        new_password=body.new_password,
    )
    try:
        await svc.change_password(cmd)
    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except UnauthorizedException as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message)
    return Response(status_code=status.HTTP_204_NO_CONTENT)