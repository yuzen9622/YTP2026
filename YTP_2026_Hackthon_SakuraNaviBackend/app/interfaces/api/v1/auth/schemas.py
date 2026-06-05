"""Pydantic schemas for auth endpoints."""
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.interfaces.api.v1.validators import validate_career, validate_gender, validate_tags


class RegisterRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "櫻花太郎",
                "account": "sakura_taro",
                "password": "Secure123",
                "email": "sakura@example.com",
                "phone": "+886912345678",
                "birth_date": "2000-01-15",
                "career": "employed",
                "tags": ["旅遊", "美食", "科技"],
                "gender": "male",
            }
        }
    )

    name: str = Field(..., min_length=1, max_length=100, description="顯示名稱")
    account: str = Field(
        ..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$", description="帳號（3–50 字元，僅限英數字與底線）"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="密碼（需含大寫字母、小寫字母及數字，8–128 字元）",
    )
    email: Optional[EmailStr] = Field(None, description="電子郵件（選填）")
    phone: Optional[str] = Field(None, description="手機號碼（選填，含國碼，如 +886912345678）")
    birth_date: Optional[date] = Field(None, description="出生年月日（選填，YYYY-MM-DD）")
    career: Optional[str] = Field(None, description="職業狀態（選填：`unemployed` / `employed` / `student`）")
    tags: Optional[List[str]] = Field(None, description="關鍵詞標籤（選填，最多 20 筆，每筆最多 50 字元）")
    gender: Optional[str] = Field(None, description="性別（選填：`male` / `female` / `hidden`）")

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
            raise ValueError("密碼不符合複雜度要求：" + "、".join(errors))
        return v

    @field_validator("career")
    @classmethod
    def career_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        return validate_career(v)

    @field_validator("tags")
    @classmethod
    def tags_must_be_valid(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        return validate_tags(v)

    @field_validator("gender")
    @classmethod
    def gender_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        return validate_gender(v)


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "account": "sakura_taro",
                "password": "Secure123",
            }
        }
    )

    account: str = Field(..., description="帳號")
    password: str = Field(..., description="密碼")


class RefreshRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyX2lkIiwiZXhwIjoxNzQ1MDAwMDAwfQ.signature",
            }
        }
    )

    refresh_token: str = Field(..., description="登入時取得的 Refresh Token")


class TokenResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyX2lkIiwiZXhwIjoxNzQ1MDAwMDAwfQ.signature",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyX2lkIiwiZXhwIjoxNzQ3MDAwMDAwfQ.signature",
                "token_type": "bearer",
            }
        }
    )

    access_token: str = Field(..., description="JWT Access Token（短效）")
    refresh_token: str = Field(..., description="JWT Refresh Token（長效，每次刷新後自動輪換）")
    token_type: str = Field(default="bearer", description="Token 類型")


class AdminLoginRequest(BaseModel):
    """POST /auth/admin/login request body."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "account": "admin_sakura",
                "password": "SecureAdmin123",
            }
        }
    )

    account: str = Field(..., description="管理者帳號")
    password: str = Field(..., description="密碼")


class AdminTokenResponse(BaseModel):
    """POST /auth/admin/login response body."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.admin.signature",
                "token_type": "bearer",
            }
        }
    )

    access_token: str = Field(..., description="Admin JWT Access Token")
    token_type: str = Field(default="bearer", description="Token 類型")
