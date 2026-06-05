"""Shared Pydantic field validators reused across v1 schemas."""
from typing import List, Optional

from app.domains.user.value_objects import CareerStatus, GenderStatus


def validate_career(v: Optional[str]) -> Optional[str]:
    """Validate that *v* is a recognised CareerStatus value (or None)."""
    if v is not None:
        try:
            CareerStatus(v)
        except ValueError:
            raise ValueError("職業狀態必須為 'unemployed'、'employed' 或 'student'")
    return v


def validate_gender(v: Optional[str]) -> Optional[str]:
    """Validate that *v* is a recognised GenderStatus value (or None)."""
    if v is not None:
        try:
            GenderStatus(v)
        except ValueError:
            raise ValueError("性別必須為 'male'、'female' 或 'hidden'")
    return v


def validate_tags(v: Optional[List[str]]) -> Optional[List[str]]:
    """Validate tag list: max 20 entries, each non-empty and ≤ 50 characters."""
    if v is None:
        return v
    if len(v) > 20:
        raise ValueError("標籤不能超過 20 筆")
    for tag in v:
        if not tag or not tag.strip():
            raise ValueError("標籤不能為空字串")
        if len(tag) > 50:
            raise ValueError(f"標籤 '{tag}' 超過 50 字元上限")
    return v
