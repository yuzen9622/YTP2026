from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from app.domains.user.value_objects import (
    UserId,
    UserName,
    Account,
    HashedPassword,
    Email,
    Phone,
    UserBio,
    UserCreatedAt,
    UserUpdatedAt,
    UserBirthDate,
    UserCareer,
    UserTags,
    AvatarUrl,
    LanguageSkill,
    LanguageSkills,
    LanguageProficiency,
    CareerStatus,
    GenderStatus,
    UserGender,
    UserRole,
    UserRoleStatus,
)
from app.domains.user.exceptions import (
    UserAlreadyInactiveException,
    UserAlreadyActiveException,
)

_DEFAULT_BIO = "這位使用者尚未填寫個人簡介。"


@dataclass
class User:
    """User aggregate root.

    All state changes must go through domain methods.
    No public setters. All attributes are private.
    """
    _id: UserId
    _name: UserName
    _account: Account
    _hashed_password: HashedPassword
    _email: Optional[Email]
    _phone: Optional[Phone]
    _created_at: UserCreatedAt
    _updated_at: UserUpdatedAt
    _bio: UserBio
    _is_active: bool
    _deleted_at: Optional[datetime]
    _birth_date: Optional[UserBirthDate]
    _career: Optional[UserCareer]
    _tags: UserTags
    _avatar_url: Optional[AvatarUrl]
    _language_skills: LanguageSkills
    _gender: Optional[UserGender]
    _registered_address: Optional[str]
    _residential_address: Optional[str]
    _is_residential_same_as_registered: bool
    _role: UserRole

    def __init__(
        self,
        id: UserId,
        name: UserName,
        account: Account,
        hashed_password: HashedPassword,
        email: Optional[Email],
        phone: Optional[Phone],
        created_at: datetime,
        bio: str = _DEFAULT_BIO,
        birth_date: Optional[date] = None,
        career: Optional[str] = None,
        tags: Optional[list] = None,
        avatar_url: Optional[str] = None,
        language_skills: Optional[list] = None,
        registered_address: Optional[str] = None,
        residential_address: Optional[str] = None,
        is_residential_same_as_registered: bool = False,
        gender: Optional[str] = None,
        role: Optional[str] = None,
    ) -> None:
        self._id = id
        self._name = name
        self._account = account
        self._hashed_password = hashed_password
        self._email = email
        self._phone = phone
        self._created_at = UserCreatedAt(created_at)
        self._updated_at = UserUpdatedAt(created_at)
        self._bio = UserBio(bio)
        self._is_active = True
        self._deleted_at = None
        self._birth_date = UserBirthDate(birth_date) if birth_date is not None else None
        self._career = UserCareer(CareerStatus(career)) if career is not None else None
        self._tags = UserTags(tuple(tags)) if tags is not None else UserTags(())
        self._avatar_url = AvatarUrl(avatar_url) if avatar_url is not None else None
        if language_skills is not None:
            skills_tuple = tuple(
                LanguageSkill(lang, LanguageProficiency(prof) if isinstance(prof, str) else prof)
                for lang, prof in language_skills
            )
            self._language_skills = LanguageSkills(skills_tuple)
        else:
            self._language_skills = LanguageSkills(())
        self._registered_address = registered_address
        self._residential_address = residential_address
        self._is_residential_same_as_registered = is_residential_same_as_registered
        self._gender = UserGender(GenderStatus(gender)) if gender is not None else None
        self._role = UserRole(UserRoleStatus(role)) if role is not None else UserRole(UserRoleStatus.USER)

    def id(self) -> UserId:
        return self._id

    # --- Getters (read-only access) ---

    def name(self) -> UserName:
        return self._name

    def account(self) -> Account:
        return self._account

    def hashed_password(self) -> HashedPassword:
        return self._hashed_password

    def email(self) -> Optional[Email]:
        return self._email

    def phone(self) -> Optional[Phone]:
        return self._phone

    def bio(self) -> UserBio:
        return self._bio

    def birth_date(self) -> Optional[UserBirthDate]:
        return self._birth_date

    def career(self) -> Optional[UserCareer]:
        return self._career

    def tags(self) -> UserTags:
        return self._tags

    def avatar_url(self) -> Optional[AvatarUrl]:
        return self._avatar_url

    def language_skills(self) -> LanguageSkills:
        return self._language_skills

    def gender(self) -> Optional[UserGender]:
        return self._gender

    def role(self) -> UserRole:
        return self._role

    def registered_address(self) -> Optional[str]:
        return self._registered_address

    def residential_address(self) -> Optional[str]:
        return self._residential_address

    def is_residential_same_as_registered(self) -> bool:
        return self._is_residential_same_as_registered

    def is_active(self) -> bool:
        return self._is_active

    def is_deleted(self) -> bool:
        return not self._is_active

    def deleted_at(self) -> Optional[datetime]:
        return self._deleted_at

    def created_at(self) -> datetime:
        return self._created_at.value

    def updated_at(self) -> datetime:
        return self._updated_at.value

    # --- Domain Methods (state change via behavior) ---

    def update_bio(self, new_bio: str, now: datetime) -> None:
        """Update user biography."""
        self._bio = UserBio(new_bio)
        self._updated_at = UserUpdatedAt(now)

    def update_name(self, new_name: UserName, now: datetime) -> None:
        """Update user display name."""
        self._name = new_name
        self._updated_at = UserUpdatedAt(now)

    def change_email(self, new_email: Email, now: datetime) -> None:
        """Change user email address."""
        self._email = new_email
        self._updated_at = UserUpdatedAt(now)

    def change_phone(self, new_phone: Phone, now: datetime) -> None:
        """Change user phone number."""
        self._phone = new_phone
        self._updated_at = UserUpdatedAt(now)

    def clear_email(self, now: datetime) -> None:
        """Clear user email address."""
        self._email = None
        self._updated_at = UserUpdatedAt(now)

    def clear_phone(self, now: datetime) -> None:
        """Clear user phone number."""
        self._phone = None
        self._updated_at = UserUpdatedAt(now)

    def update_birth_date(self, new_birth_date: Optional[date], now: datetime) -> None:
        """Update user birth date (None to clear)."""
        self._birth_date = UserBirthDate(new_birth_date) if new_birth_date is not None else None
        self._updated_at = UserUpdatedAt(now)

    def update_career(self, new_career: Optional[str], now: datetime) -> None:
        """Update or clear user career status (None to clear)."""
        if new_career is None:
            self._career = None
        else:
            self._career = UserCareer(CareerStatus(new_career))
        self._updated_at = UserUpdatedAt(now)

    def change_password(self, new_hashed_password: HashedPassword, now: datetime) -> None:
        """Replace the stored password hash with a new one."""
        self._hashed_password = new_hashed_password
        self._updated_at = UserUpdatedAt(now)

    def update_tags(self, new_tags: list, now: datetime) -> None:
        """Replace user tags with a new list."""
        self._tags = UserTags(tuple(new_tags))
        self._updated_at = UserUpdatedAt(now)

    def update_avatar_url(self, new_avatar_url: Optional[str], now: datetime) -> None:
        """Update user avatar URL (None to clear)."""
        self._avatar_url = AvatarUrl(new_avatar_url) if new_avatar_url is not None else None
        self._updated_at = UserUpdatedAt(now)

    def update_language_skills(self, new_skills: list, now: datetime) -> None:
        """Replace user language skills with a new list."""
        skills_tuple = tuple(
            LanguageSkill(lang, LanguageProficiency(prof) if isinstance(prof, str) else prof)
            for lang, prof in new_skills
        )
        self._language_skills = LanguageSkills(skills_tuple)
        self._updated_at = UserUpdatedAt(now)

    def update_registered_address(self, new_address: Optional[str], now: datetime) -> None:
        """Update or clear registered address (household registration)."""
        self._registered_address = new_address
        self._updated_at = UserUpdatedAt(now)

    def update_residential_address(self, new_address: Optional[str], now: datetime) -> None:
        """Update or clear residential address (current living address)."""
        self._residential_address = new_address
        self._updated_at = UserUpdatedAt(now)

    def update_is_residential_same_as_registered(self, value: bool, now: datetime) -> None:
        """Set whether residential address is the same as registered address."""
        self._is_residential_same_as_registered = value
        self._updated_at = UserUpdatedAt(now)

    def update_gender(self, new_gender: Optional[str], now: datetime) -> None:
        """Update user gender (None to clear)."""
        self._gender = UserGender(GenderStatus(new_gender)) if new_gender is not None else None
        self._updated_at = UserUpdatedAt(now)

    def update_role(self, new_role: UserRole, now: datetime) -> None:
        """Update user platform role."""
        self._role = new_role
        self._updated_at = UserUpdatedAt(now)

    def deactivate(self, now: datetime) -> None:
        """Deactivate user account (soft delete)."""
        if not self._is_active:
            raise UserAlreadyInactiveException("User is already inactive")
        self._is_active = False
        self._deleted_at = now
        self._updated_at = UserUpdatedAt(now)

    def activate(self, now: datetime) -> None:
        """Reactivate previously deactivated user."""
        if self._is_active:
            raise UserAlreadyActiveException("User is already active")
        self._is_active = True
        self._deleted_at = None
        self._updated_at = UserUpdatedAt(now)

    # --- Persistence reconstruction (repository layer only) ---

    @classmethod
    def _restore(
        cls,
        *,
        id: UserId,
        name: UserName,
        account: Account,
        hashed_password: HashedPassword,
        email: Optional[Email],
        phone: Optional[Phone],
        bio: str,
        created_at: datetime,
        updated_at: datetime,
        is_active: bool,
        deleted_at: Optional[datetime],
        birth_date: Optional[date] = None,
        career: Optional[str] = None,
        tags: Optional[list] = None,
        avatar_url: Optional[str] = None,
        language_skills: Optional[list] = None,
        registered_address: Optional[str] = None,
        residential_address: Optional[str] = None,
        is_residential_same_as_registered: bool = False,
        gender: Optional[str] = None,
        role: Optional[str] = None,
    ) -> "User":
        """Reconstitute a User from persisted state.

        For repository use only — bypasses the domain constructor so that
        mutable fields (updated_at, is_active, deleted_at) can be restored
        without breaking encapsulation through direct attribute mutation.
        """
        obj: "User" = cls.__new__(cls)
        obj._id = id
        obj._name = name
        obj._account = account
        obj._hashed_password = hashed_password
        obj._email = email
        obj._phone = phone
        obj._bio = UserBio(bio)
        obj._created_at = UserCreatedAt(created_at)
        obj._updated_at = UserUpdatedAt(updated_at)
        obj._is_active = is_active
        obj._deleted_at = None if is_active else deleted_at
        obj._birth_date = UserBirthDate(birth_date) if birth_date is not None else None
        obj._career = UserCareer(CareerStatus(career)) if career is not None else None
        obj._tags = UserTags(tuple(tags)) if tags is not None else UserTags(())
        obj._avatar_url = AvatarUrl(avatar_url) if avatar_url is not None else None
        if language_skills is not None:
            skills_tuple = tuple(
                LanguageSkill(lang, LanguageProficiency(prof) if isinstance(prof, str) else prof)
                for lang, prof in language_skills
            )
            obj._language_skills = LanguageSkills(skills_tuple)
        else:
            obj._language_skills = LanguageSkills(())
        obj._registered_address = registered_address
        obj._residential_address = residential_address
        obj._is_residential_same_as_registered = is_residential_same_as_registered
        obj._gender = UserGender(GenderStatus(gender)) if gender is not None else None
        obj._role = UserRole(UserRoleStatus(role)) if role is not None else UserRole(UserRoleStatus.USER)
        return obj
