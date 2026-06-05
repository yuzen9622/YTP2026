import enum
import re
import uuid
import phonenumbers
from dataclasses import dataclass
from datetime import date, datetime
from email_validator import EmailNotValidError, validate_email
from typing import TypeAlias

# @dataclass(frozen=True) auto-generates correct __eq__ and __hash__ for all
# value objects — no per-class boilerplate needed.


@dataclass(frozen=True)
class UserTimestamp:
    """Timestamp value object (used for both created_at and updated_at)."""

    value: datetime

    def __post_init__(self):
        if not isinstance(self.value, datetime):
            raise ValueError("Timestamp must be a datetime")
        if self.value.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware (use datetime.now(tz=timezone.utc))")


# TypeAlias makes intent explicit: these are structural aliases, not distinct types.
UserCreatedAt: TypeAlias = UserTimestamp
UserUpdatedAt: TypeAlias = UserTimestamp


@dataclass(frozen=True)
class UserId:
    """User entity unique identifier."""
    value: uuid.UUID

    def __post_init__(self):
        if not isinstance(self.value, uuid.UUID):
            raise ValueError(f"Invalid UserId: {self.value}")


@dataclass(frozen=True)
class Email:
    """User email value object."""
    value: str

    def __post_init__(self):
        try:
            result = validate_email(self.value, check_deliverability=False)
            object.__setattr__(self, "value", result.normalized)
        except EmailNotValidError:
            raise ValueError(f"Invalid email: {self.value}")


@dataclass(frozen=True)
class Phone:
    """User phone number value object."""
    value: str

    def __post_init__(self):
        try:
            parsed = phonenumbers.parse(self.value, None)
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError(f"Invalid phone number: {self.value}")
            normalized = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            object.__setattr__(self, "value", normalized)
        except phonenumbers.NumberParseException:
            raise ValueError(f"Invalid phone number format: {self.value}")


@dataclass(frozen=True)
class HashedPassword:
    """User hashed password value object."""
    value: str

    def __post_init__(self):
        if not self.value.startswith("$2b$") or len(self.value) != 60:
            raise ValueError("Invalid hashed password format")


@dataclass(frozen=True)
class UserBio:
    """User biography value object."""
    value: str

    def __post_init__(self):
        if len(self.value) > 500:
            raise ValueError("Bio cannot exceed 500 characters")


@dataclass(frozen=True)
class UserName:
    """User display name value object."""
    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("User name cannot be empty")
        if len(self.value) > 100:
            raise ValueError("User name cannot exceed 100 characters")


@dataclass(frozen=True)
class Account:
    """User account identifier value object."""
    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("Account cannot be empty")
        if len(self.value) > 50:
            raise ValueError("Account cannot exceed 50 characters")
        if not re.match(r"^[a-zA-Z0-9_]+$", self.value):
            raise ValueError("Account can only contain alphanumeric and underscore")


class CareerStatus(str, enum.Enum):
    """User career status."""
    UNEMPLOYED = "unemployed"
    EMPLOYED = "employed"
    STUDENT = "student"


class GenderStatus(str, enum.Enum):
    """User gender (biological sex registration only)."""
    MALE = "male"
    FEMALE = "female"
    HIDDEN = "hidden"



@dataclass(frozen=True)
class UserBirthDate:
    """User birth date value object."""
    value: date

    def __post_init__(self):
        if not isinstance(self.value, date):
            raise ValueError("Birth date must be a date")
        if self.value > date.today():
            raise ValueError("Birth date cannot be in the future")
        age = (date.today() - self.value).days / 365.25
        if not (0 <= age <= 150):
            raise ValueError(f"Birth date results in age {age:.0f}, which is outside valid range 0-150")


@dataclass(frozen=True)
class UserCareer:
    """User career status value object."""
    value: CareerStatus

    def __post_init__(self):
        if not isinstance(self.value, CareerStatus):
            raise ValueError(f"Invalid career status: {self.value}. Must be 'unemployed', 'employed' or 'student'.")


@dataclass(frozen=True)
class UserGender:
    """User gender value object (biological sex only — male, female, or hidden)."""
    value: GenderStatus

    def __post_init__(self):
        if not isinstance(self.value, GenderStatus):
            raise ValueError(f"Invalid gender: {self.value}. Must be 'male', 'female' or 'hidden'.")


@dataclass(frozen=True)
class AvatarUrl:
    """User avatar URL value object."""
    value: str

    def __post_init__(self):
        if not self.value.startswith(("http://", "https://")):
            raise ValueError("Avatar URL must start with http:// or https://")
        if len(self.value) > 512:
            raise ValueError("Avatar URL cannot exceed 512 characters")


class LanguageProficiency(str, enum.Enum):
    """Language proficiency level."""
    NATIVE = "native"
    ADVANCED = "advanced"
    UPPER_INTERMEDIATE = "upper_intermediate"
    INTERMEDIATE = "intermediate"
    BASIC = "basic"


@dataclass(frozen=True)
class LanguageSkill:
    """A single language skill (language code + proficiency)."""
    language: str
    proficiency: LanguageProficiency

    def __post_init__(self):
        if not self.language or len(self.language.strip()) == 0:
            raise ValueError("Language code cannot be empty")
        if len(self.language) > 10:
            raise ValueError(f"Language code '{self.language}' exceeds 10 characters")


@dataclass(frozen=True)
class LanguageSkills:
    """User language skills value object (immutable tuple)."""
    value: tuple[LanguageSkill, ...]

    def __post_init__(self):
        if len(self.value) > 10:
            raise ValueError("Language skills cannot exceed 10 items")
        for skill in self.value:
            if not isinstance(skill, LanguageSkill):
                raise ValueError(f"Invalid language skill: {skill}")


@dataclass(frozen=True)
class UserTags:
    """User tags value object (immutable tuple of keyword strings)."""
    value: tuple

    def __post_init__(self):
        if len(self.value) > 20:
            raise ValueError("Tags cannot exceed 20 items")
        for tag in self.value:
            if not tag or len(tag.strip()) == 0:
                raise ValueError("Tag cannot be empty")
            if len(tag) > 50:
                raise ValueError(f"Tag '{tag}' exceeds 50 characters")


class UserRoleStatus(str, enum.Enum):
    """User role enum (platform-level role for the user account)."""
    USER = "user"


@dataclass(frozen=True)
class UserRole:
    """User role value object."""
    value: UserRoleStatus

    def __post_init__(self):
        if not isinstance(self.value, UserRoleStatus):
            raise ValueError(f"Invalid user role: {self.value}. Must be one of: {[r.value for r in UserRoleStatus]}")