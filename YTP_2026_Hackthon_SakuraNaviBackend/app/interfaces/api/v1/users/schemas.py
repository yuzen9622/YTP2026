"""Pydantic schemas for user endpoints."""
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.interfaces.api.v1.validators import validate_career, validate_gender, validate_tags


class LanguageSkillInput(BaseModel):
    language: str = Field(..., min_length=1, max_length=10, description="語言代碼，如 'en', 'ja', 'zh'")
    proficiency: str = Field(
        ...,
        description="語言能力等級：native / advanced / upper_intermediate / intermediate / basic",
    )


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "櫻花太郎",
                "account": "sakura_taro",
                "email": "sakura@example.com",
                "phone": "+886912345678",
                "bio": "熱愛技術的開發者",
                "birth_date": "2000-01-15",
                "career": "employed",
                "tags": ["旅遊", "美食", "科技"],
                "avatar_url": "https://example.com/avatar.jpg",
                "language_skills": [
                    {"language": "en", "proficiency": "advanced"},
                    {"language": "ja", "proficiency": "native"},
                ],
                "registered_address": "台北市中正區公府路1號",
                "residential_address": "新北市板橋區文化路100號",
                "is_residential_same_as_registered": False,
                "is_active": True,
                "created_at": "2026-04-20T00:00:00Z",
                "updated_at": "2026-04-20T12:00:00Z",
            }
        }
    )

    id: str = Field(..., description="使用者唯一識別碼（UUID）")
    name: str = Field(..., description="顯示名稱")
    account: str = Field(..., description="帳號")
    email: Optional[str] = Field(None, description="電子郵件")
    phone: Optional[str] = Field(None, description="手機號碼（含國碼）")
    bio: str = Field(..., description="個人簡介")
    birth_date: Optional[date] = Field(None, description="出生年月日（YYYY-MM-DD）")
    career: Optional[str] = Field(None, description="職業狀態（`unemployed` / `employed` / `student`）")
    tags: List[str] = Field(default_factory=list, description="關鍵詞標籤清單")
    avatar_url: Optional[str] = Field(None, description="頭貼網址")
    language_skills: List[dict] = Field(
        default_factory=list,
        description="語言能力清單，如 [{\"language\": \"en\", \"proficiency\": \"advanced\"}]",
    )
    registered_address: Optional[str] = Field(None, description="戶籍地址")
    residential_address: Optional[str] = Field(None, description="居住地址")
    is_residential_same_as_registered: bool = Field(False, description="居住地址與戶籍地址相同")
    gender: Optional[str] = Field(None, description="性別（male / female / hidden）")
    is_active: bool = Field(..., description="帳號是否啟用")
    created_at: datetime = Field(..., description="帳號建立時間（ISO 8601）")
    updated_at: datetime = Field(..., description="帳號最後更新時間（ISO 8601）")


class UpdateProfileRequest(BaseModel):
    """PATCH /users/me request body — all fields optional; omit to keep unchanged.

    - ``email`` / ``phone`` / ``birth_date`` / ``career`` / ``avatar_url``: pass ``null`` to clear.
    - ``tags``: pass empty list to clear all tags.
    - ``language_skills``: pass empty list to clear all language skills.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "新名字",
                "bio": "更新後的自我介紹",
                "email": "new@example.com",
                "phone": "+886987654321",
                "birth_date": "2000-01-15",
                "career": "employed",
                "tags": ["旅遊", "科技"],
                "avatar_url": "https://example.com/avatar.jpg",
                "language_skills": [
                    {"language": "en", "proficiency": "advanced"},
                ],
                "registered_address": "台北市中正區公府路1號",
                "residential_address": "新北市板橋區文化路100號",
                "is_residential_same_as_registered": False,
            }
        }
    )

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="顯示名稱")
    bio: Optional[str] = Field(None, max_length=500, description="個人簡介（最多 500 字元）")
    email: Optional[EmailStr] = Field(None, description="電子郵件（傳 null 可清除）")
    phone: Optional[str] = Field(None, description="手機號碼（含國碼，如 +886912345678；傳 null 可清除）")
    birth_date: Optional[date] = Field(None, description="出生年月日（YYYY-MM-DD；傳 null 可清除）")
    career: Optional[str] = Field(None, description="職業狀態（`unemployed` / `employed` / `student`；傳 null 可清除）")
    tags: Optional[List[str]] = Field(
        None,
        description="標籤列表（最多 20 筆，每筆最多 50 字元，不可為空字串；傳空陣列可清除）",
    )
    avatar_url: Optional[str] = Field(
        None,
        max_length=512,
        description="頭貼網址（需以 http:// 或 https:// 開頭；傳 null 可清除）",
    )
    language_skills: Optional[List[LanguageSkillInput]] = Field(
        None,
        description="語言能力列表（最多 10 筆；傳空陣列可清除）",
    )
    registered_address: Optional[str] = Field(
        None,
        max_length=255,
        description="戶籍地址（傳 null 可清除）",
    )
    residential_address: Optional[str] = Field(
        None,
        max_length=255,
        description="居住地址（傳 null 可清除）",
    )
    is_residential_same_as_registered: Optional[bool] = Field(
        None,
        description="居住地址是否與戶籍地址相同",
    )
    gender: Optional[str] = Field(
        None,
        description="性別（male / female / hidden；傳 null 可清除）",
    )

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


class ChangePasswordRequest(BaseModel):
    """PUT /users/me/password request body."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_password": "OldPass123",
                "new_password": "NewPass456",
            }
        }
    )

    current_password: str = Field(..., description="目前密碼")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="新密碼（需含大寫字母、小寫字母及數字，8–128 字元）",
    )

    @field_validator("new_password")
    @classmethod
    def new_password_complexity(cls, v: str) -> str:
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
            raise ValueError("新密碼複雜度不足：" + "；".join(errors))
        return v


class AdminUserListResponse(BaseModel):
    """GET /admin/users response body."""
    items: List["UserProfileResponse"] = Field(description="使用者列表")
    total: int = Field(description="符合條件的總筆數")
    limit: int = Field(description="本頁回傳筆數上限")
    offset: int = Field(description="跳過的筆數（分頁偏移）")


class AdminUpdateUserRequest(BaseModel):
    """PATCH /admin/users/{user_id} request body — all fields optional; omit to keep unchanged.

    - ``email`` / ``phone`` / ``birth_date`` / ``career`` / ``avatar_url``: pass ``null`` to clear.
    - ``tags``: pass empty list to clear all tags.
    - ``language_skills``: pass empty list to clear all language skills.
    - ``password``: plain text; will be hashed before storage.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "新名字",
                "is_active": False,
            }
        }
    )

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="顯示名稱")
    bio: Optional[str] = Field(None, max_length=500, description="個人簡介（最多 500 字元）")
    email: Optional[EmailStr] = Field(None, description="電子郵件（傳 null 可清除）")
    phone: Optional[str] = Field(None, description="手機號碼（含國碼，如 +886912345678；傳 null 可清除）")
    birth_date: Optional[date] = Field(None, description="出生年月日（YYYY-MM-DD；傳 null 可清除）")
    career: Optional[str] = Field(None, description="職業狀態（`unemployed` / `employed` / `student`；傳 null 可清除）")
    tags: Optional[List[str]] = Field(
        None,
        description="標籤列表（最多 20 筆，每筆最多 50 字元，不可為空字串；傳空陣列可清除）",
    )
    avatar_url: Optional[str] = Field(
        None,
        max_length=512,
        description="頭貼網址（需以 http:// 或 https:// 開頭；傳 null 可清除）",
    )
    language_skills: Optional[List["LanguageSkillInput"]] = Field(
        None,
        description="語言能力列表（最多 10 筆；傳空陣列可清除）",
    )
    registered_address: Optional[str] = Field(
        None,
        max_length=255,
        description="戶籍地址（傳 null 可清除）",
    )
    residential_address: Optional[str] = Field(
        None,
        max_length=255,
        description="居住地址（傳 null 可清除）",
    )
    is_residential_same_as_registered: Optional[bool] = Field(
        None,
        description="居住地址是否與戶籍地址相同",
    )
    gender: Optional[str] = Field(
        None,
        description="性別（male / female / hidden；傳 null 可清除）",
    )
    is_active: Optional[bool] = Field(
        None,
        description="帳號是否啟用（false = 停用，類似軟刪除）",
    )
    role: Optional[str] = Field(
        None,
        description="角色（`user` 或 `admin`）",
    )
    password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=128,
        description="新密碼（需含大寫字母、小寫字母及數字，8–128 字元）",
    )

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

    @field_validator("password")
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
