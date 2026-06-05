"""Pydantic schemas for resume endpoints."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class WorkExperienceInput(BaseModel):
    company: str = Field(..., max_length=100, description="公司名稱")
    position: str = Field(..., max_length=100, description="職位")
    description: str = Field("", max_length=1000, description="工作描述")
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}$", description="開始年月 YYYY-MM")
    end_date: str = Field("present", description="結束年月 YYYY-MM 或 'present'")
    is_current: bool = Field(False, description="是否為現職")


class ExternalLinkInput(BaseModel):
    label: str = Field(..., max_length=50, description="連結標籤，如 'GitHub'、'LinkedIn'")
    url: str = Field(..., max_length=512, description="連結網址")


class ExpectedSalaryInput(BaseModel):
    min: int = Field(..., ge=0, description="最低期望薪資")
    max: int = Field(..., ge=0, description="最高期望薪資")
    currency: str = Field(..., min_length=3, max_length=3, description="幣別，如 TWD、USD、JPY")


class WorkTimeRangeInput(BaseModel):
    start_time: str = Field("09:00", pattern=r"^\d{2}:\d{2}$", description="上班時間 HH:MM")
    end_time: str = Field("18:00", pattern=r"^\d{2}:\d{2}$", description="下班時間 HH:MM")
    work_time_type: str = Field(
        ...,
        description="工作時間類型：full_time / part_time / internship / freelance",
    )


class SkillInput(BaseModel):
    name: str = Field(..., max_length=50, description="技能名稱")
    level: str = Field("intermediate", description="熟练程度")


class CreateResumeRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "軟體工程師履歷",
                "summary": "熱愛程式開發，擅長 Python 與 JavaScript",
                "skills": [
                    {"name": "Python", "level": "advanced"},
                    {"name": "JavaScript", "level": "intermediate"},
                ],
                "work_experiences": [
                    {
                        "company": "ABC Corp",
                        "position": "軟體工程師",
                        "description": "開發 RESTful API",
                        "start_date": "2023-01",
                        "end_date": "present",
                        "is_current": True,
                    }
                ],
                "external_links": [
                    {"label": "GitHub", "url": "https://github.com/example"},
                ],
                "expected_salary": {"min": 50000, "max": 80000, "currency": "TWD"},
                "work_time_range": {
                    "start_time": "09:00",
                    "end_time": "18:00",
                    "work_time_type": "full_time",
                },
            }
        }
    )

    title: str = Field(..., min_length=1, max_length=100, description="履歷標題")
    summary: Optional[str] = Field(None, max_length=2000, description="簡述")
    skills: Optional[List[SkillInput]] = Field(None, description="專業技能列表（最多 50 筆）")
    work_experiences: Optional[List[WorkExperienceInput]] = Field(None, description="工作經驗列表")
    external_links: Optional[List[ExternalLinkInput]] = Field(None, description="外部連結列表")
    expected_salary: Optional[ExpectedSalaryInput] = Field(None, description="期望薪資")
    work_time_range: Optional[WorkTimeRangeInput] = Field(None, description="工作時間段")


class UpdateResumeRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "更新後的履歷標題",
                "summary": "更新後的簡述",
            }
        }
    )

    title: Optional[str] = Field(None, min_length=1, max_length=100, description="履歷標題")
    summary: Optional[str] = Field(None, max_length=2000, description="簡述")
    skills: Optional[List[SkillInput]] = Field(None, description="專業技能列表")
    work_experiences: Optional[List[WorkExperienceInput]] = Field(None, description="工作經驗列表")
    external_links: Optional[List[ExternalLinkInput]] = Field(None, description="外部連結列表")
    expected_salary: Optional[ExpectedSalaryInput] = Field(None, description="期望薪資")
    work_time_range: Optional[WorkTimeRangeInput] = Field(None, description="工作時間段")


class ResumeResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "軟體工程師履歷",
                "summary": "熱愛程式開發",
                "skills": [{"name": "Python", "level": "advanced"}],
                "work_experiences": [],
                "external_links": [{"label": "GitHub", "url": "https://github.com/example"}],
                "expected_salary": {"min": 50000, "max": 80000, "currency": "TWD"},
                "work_time_range": {
                    "start_time": "09:00",
                    "end_time": "18:00",
                    "work_time_type": "full_time",
                },
                "is_primary": True,
                "created_at": "2026-04-20T00:00:00Z",
                "updated_at": "2026-04-20T12:00:00Z",
            }
        }
    )

    id: str = Field(..., description="履歷唯一識別碼")
    user_id: str = Field(..., description="擁有者使用者 ID")
    title: str = Field(..., description="履歷標題")
    summary: Optional[str] = Field(None, description="簡述")
    skills: List[dict] = Field(default_factory=list, description="專業技能")
    work_experiences: List[dict] = Field(default_factory=list, description="工作經驗")
    external_links: List[dict] = Field(default_factory=list, description="外部連結")
    expected_salary: Optional[dict] = Field(None, description="期望薪資")
    work_time_range: Optional[dict] = Field(None, description="工作時間段")
    is_primary: bool = Field(..., description="是否為主要履歷")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")
