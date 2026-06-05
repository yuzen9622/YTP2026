"""Pydantic schemas for admin endpoints."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreateAdminRequest(BaseModel):
    """POST /admin/admins request body — superadmin only."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "account": "new_admin",
                "password": "SecureAdmin123",
                "role": "customer_service",
            }
        }
    )

    account: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="管理者帳號（3–50 字元，僅限英數字與底線）",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="密碼（需含大寫字母、小寫字母及數字，8–128 字元）",
    )
    role: str = Field(
        ...,
        description="管理者職位：superadmin / customer_service / security_reviewer / content_manager",
    )

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        has_upper = has_lower = has_digit = False
        for c in v:
            if c.isupper():
                has_upper = True
            if c.islower():
                has_lower = True
            if c.isdigit():
                has_digit = True
            if has_upper and has_lower and has_digit:
                break
        errors: list[str] = []
        if not has_upper:
            errors.append("需含至少一個大寫字母")
        if not has_lower:
            errors.append("需含至少一個小寫字母")
        if not has_digit:
            errors.append("需含至少一個數字")
        if errors:
            raise ValueError("密碼複雜度不足：" + "；".join(errors))
        return v

    @field_validator("role")
    @classmethod
    def role_must_be_valid(cls, v: str) -> str:
        valid = ("superadmin", "customer_service", "security_reviewer", "content_manager")
        if v not in valid:
            raise ValueError(f"role must be one of: {', '.join(valid)}")
        return v


class AdminResponse(BaseModel):
    """Admin record response."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "account": "admin_user",
                "role": "customer_service",
                "is_active": True,
                "created_at": "2026-04-26T10:00:00Z",
                "updated_at": "2026-04-26T10:00:00Z",
            }
        }
    )

    id: str = Field(description="Admin ID")
    account: str = Field(description="帳號")
    role: str = Field(description="職位：superadmin / customer_service / security_reviewer / content_manager")
    is_active: bool = Field(description="是否啟用")
    created_at: datetime = Field(description="建立時間")
    updated_at: datetime = Field(description="最後更新時間")


class AdminListResponse(BaseModel):
    """GET /admin/admins response body."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "account": "admin_user",
                        "role": "customer_service",
                        "is_active": True,
                        "created_at": "2026-04-26T10:00:00Z",
                        "updated_at": "2026-04-26T10:00:00Z",
                    }
                ],
                "total": 1,
                "limit": 20,
                "offset": 0,
            }
        }
    )

    items: List[AdminResponse] = Field(description="管理者列表")
    total: int = Field(description="總筆數")
    limit: int = Field(description="本頁回傳筆數上限")
    offset: int = Field(description="跳過的筆數（分頁偏移）")


class UpdateAdminRequest(BaseModel):
    """PATCH /admin/admins/{admin_id} request body."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "content_manager",
                "is_active": True,
                "new_password": None,
            }
        }
    )

    role: Optional[str] = Field(
        None,
        description="新職位：superadmin / customer_service / security_reviewer / content_manager",
    )
    is_active: Optional[bool] = Field(None, description="是否啟用")
    new_password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=128,
        description="新密碼（需含大寫字母、小寫字母及數字，8–128 字元）",
    )

    @field_validator("role")
    @classmethod
    def role_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid = ("superadmin", "customer_service", "security_reviewer", "content_manager")
        if v not in valid:
            raise ValueError(f"role must be one of: {', '.join(valid)}")
        return v

    @field_validator("new_password")
    @classmethod
    def password_complexity(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        has_upper = has_lower = has_digit = False
        for c in v:
            if c.isupper():
                has_upper = True
            if c.islower():
                has_lower = True
            if c.isdigit():
                has_digit = True
            if has_upper and has_lower and has_digit:
                break
        errors: list[str] = []
        if not has_upper:
            errors.append("需含至少一個大寫字母")
        if not has_lower:
            errors.append("需含至少一個小寫字母")
        if not has_digit:
            errors.append("需含至少一個數字")
        if errors:
            raise ValueError("密碼複雜度不足：" + "；".join(errors))
        return v