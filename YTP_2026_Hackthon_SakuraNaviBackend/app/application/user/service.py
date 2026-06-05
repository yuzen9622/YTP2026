import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.application.user.commands import (
    AdminUpdateUserCommand,
    ChangePasswordCommand,
    ListAllUsersQuery,
    LoginCommand,
    RefreshTokenCommand,
    RegisterUserCommand,
    UpdateProfileCommand,
)
from app.application.user.dtos import (
    PaginatedUsersDTO,
    TokenPairDTO,
    UserProfileDTO,
)
from app.application.user.ports import PasswordHasher, RefreshTokenRepository, TokenService
from app.application.user.queries import GetUserProfileQuery
from app.core.config import settings
from app.core.exceptions import (
    DuplicateResourceException,
    ResourceNotFoundException,
    UnauthorizedException,
)
from app.domains.user.entity import User
from app.domains.user.repository import UserRepository
from app.domains.user.value_objects import (
    Account,
    Email,
    HashedPassword,
    LanguageProficiency,
    Phone,
    UserId,
    UserName,
)
from loguru import logger


class UserApplicationService:
    """Application service orchestrating user-related use cases.

    Handles register, login, refresh, and profile retrieval.
    All state changes go through domain entities.
    """
    def __init__(
        self,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ) -> None:
        self._user_repo = user_repo
        self._refresh_token_repo = refresh_token_repo
        self._password_hasher = password_hasher
        self._token_service = token_service

    async def register(self, cmd: RegisterUserCommand) -> UserProfileDTO:
        account_vo = Account(cmd.account)
        email_vo = Email(cmd.email) if cmd.email else None
        phone_vo = Phone(cmd.phone) if cmd.phone else None

        taken = await self._user_repo.find_taken_fields(account_vo, email_vo, phone_vo)
        if "account" in taken:
            raise DuplicateResourceException(
                f"Account '{cmd.account}' is already taken.", code="ACCOUNT_TAKEN"
            )
        if "email" in taken:
            raise DuplicateResourceException(
                f"Email '{cmd.email}' is already registered.", code="EMAIL_TAKEN"
            )
        if "phone" in taken:
            raise DuplicateResourceException(
                "Phone number is already registered.", code="PHONE_TAKEN"
            )

        hashed = self._password_hasher.hash(cmd.password)
        now = datetime.now(tz=timezone.utc)
        user = User(
            id=UserId(uuid.uuid4()),
            name=UserName(cmd.name),
            account=account_vo,
            hashed_password=HashedPassword(hashed),
            email=email_vo,
            phone=phone_vo,
            created_at=now,
            birth_date=cmd.birth_date,
            career=cmd.career,
            tags=list(cmd.tags) if cmd.tags else None,
            gender=cmd.gender,
        )

        await self._user_repo.save(user)
        logger.info("[auth] User registered: account={} user_id={}", cmd.account, user.id().value)
        return self._to_profile_dto(user)

    async def login(self, cmd: LoginCommand) -> TokenPairDTO:
        account_vo = Account(cmd.account)
        user = await self._user_repo.find_by_account(account_vo)

        # Always run bcrypt regardless of whether the account exists.
        # This prevents timing-based account enumeration: an attacker cannot
        # distinguish "account not found" from "wrong password" by measuring
        # response latency.
        check_hash = (
            user.hashed_password().value
            if user is not None
            else self._password_hasher.dummy_hash
        )
        password_ok = self._password_hasher.verify(cmd.password, check_hash)

        if user is None or not password_ok:
            logger.warning("[auth] Login failed: account={} reason=invalid_credentials", cmd.account)
            raise UnauthorizedException(
                "Invalid account or password.", code="INVALID_CREDENTIALS"
            )

        if not user.is_active():
            logger.warning("[auth] Login failed: account={} reason=account_inactive", cmd.account)
            raise UnauthorizedException(
                "Account is deactivated.", code="ACCOUNT_INACTIVE"
            )

        logger.info("[auth] Login success: account={} user_id={}", cmd.account, user.id().value)
        user_role = str(user.role().value.value) if hasattr(user.role(), "value") else str(user.role())
        return await self._issue_token_pair(str(user.id().value), role=user_role)

    async def refresh(self, cmd: RefreshTokenCommand) -> TokenPairDTO:
        try:
            user_id, jti = self._token_service.decode_refresh_token(cmd.refresh_token)
        except UnauthorizedException:
            raise

        family_id = await self._refresh_token_repo.find_family_id_by_jti(jti)
        is_valid = await self._refresh_token_repo.exists_and_valid(jti)
        if family_id is None:
            raise UnauthorizedException(
                "Refresh token not recognised.", code="REFRESH_TOKEN_NOT_FOUND"
            )

        if not is_valid:
            await self._refresh_token_repo.revoke_family(family_id)
            logger.warning(
                "[auth] Token reuse detected: user_id={} family={} — family revoked",
                user_id, family_id,
            )
            raise UnauthorizedException(
                "Refresh token has already been used. All sessions in this family have been revoked for your security.",
                code="TOKEN_REUSE_DETECTED",
            )

        logger.info("[auth] Token refresh: user_id={} jti={}", user_id, jti)
        await self._refresh_token_repo.revoke(jti)
        return await self._issue_token_pair(user_id, family_id=family_id)

    async def get_profile(self, query: GetUserProfileQuery) -> UserProfileDTO:
        user = await self._get_active_user(query.user_id)
        return self._to_profile_dto(user)

    async def update_profile(self, cmd: UpdateProfileCommand) -> UserProfileDTO:
        user = await self._get_active_user(cmd.user_id)
        now = datetime.now(tz=timezone.utc)

        if "name" in cmd.provided_fields and cmd.name is not None:
            user.update_name(UserName(cmd.name), now)

        if "bio" in cmd.provided_fields and cmd.bio is not None:
            user.update_bio(cmd.bio, now)

        if "email" in cmd.provided_fields:
            if cmd.email is None:
                user.clear_email(now)
            else:
                email_vo = Email(cmd.email)
                current_email = user.email()
                if current_email is None or current_email.value != email_vo.value:
                    if await self._user_repo.exists_by_email(email_vo):
                        raise DuplicateResourceException(
                            f"Email '{cmd.email}' is already registered.", code="EMAIL_TAKEN"
                        )
                user.change_email(email_vo, now)

        if "phone" in cmd.provided_fields:
            if cmd.phone is None:
                user.clear_phone(now)
            else:
                phone_vo = Phone(cmd.phone)
                current_phone = user.phone()
                if current_phone is None or current_phone.value != phone_vo.value:
                    if await self._user_repo.exists_by_phone(phone_vo):
                        raise DuplicateResourceException(
                            "Phone number is already registered.", code="PHONE_TAKEN"
                        )
                user.change_phone(phone_vo, now)

        if "birth_date" in cmd.provided_fields:
            user.update_birth_date(cmd.birth_date, now)

        if "career" in cmd.provided_fields:
            user.update_career(cmd.career, now)

        if "tags" in cmd.provided_fields:
            user.update_tags(list(cmd.tags), now)

        if "avatar_url" in cmd.provided_fields:
            user.update_avatar_url(cmd.avatar_url, now)

        if "language_skills" in cmd.provided_fields:
            skills_list = [
                (s["language"], LanguageProficiency(s["proficiency"]))
                for s in cmd.language_skills
            ]
            user.update_language_skills(skills_list, now)

        if "registered_address" in cmd.provided_fields:
            user.update_registered_address(cmd.registered_address, now)

        if "residential_address" in cmd.provided_fields:
            user.update_residential_address(cmd.residential_address, now)

        if "is_residential_same_as_registered" in cmd.provided_fields and cmd.is_residential_same_as_registered is not None:
            user.update_is_residential_same_as_registered(cmd.is_residential_same_as_registered, now)

        if "gender" in cmd.provided_fields:
            user.update_gender(cmd.gender, now)

        await self._user_repo.save(user)
        logger.debug("[auth] Profile updated: user_id={} fields={}", cmd.user_id, list(cmd.provided_fields))
        return self._to_profile_dto(user)

    async def change_password(self, cmd: ChangePasswordCommand) -> None:
        user = await self._get_active_user(cmd.user_id)
        if not self._password_hasher.verify(cmd.current_password, user.hashed_password().value):
            raise UnauthorizedException(
                "Current password is incorrect.", code="INVALID_CREDENTIALS"
            )
        new_hashed = self._password_hasher.hash(cmd.new_password)
        user.change_password(HashedPassword(new_hashed), datetime.now(tz=timezone.utc))
        await self._user_repo.save(user)
        logger.info("[auth] Password changed: user_id={}", cmd.user_id)

    async def _get_active_user(self, user_id_str: str) -> User:
        """Load a non-deleted user by id; raise ResourceNotFoundException if absent."""
        user_id = UserId(uuid.UUID(user_id_str))
        user = await self._user_repo.find_by_id(user_id)
        if user is None or user.is_deleted():
            raise ResourceNotFoundException(
                f"User '{user_id_str}' not found.", code="USER_NOT_FOUND"
            )
        return user

    async def _issue_token_pair(self, user_id: str, role: str = "user", family_id: Optional[str] = None) -> TokenPairDTO:
        if family_id is None:
            family_id = str(uuid.uuid4())

        access_token = self._token_service.create_access_token(user_id, role=role)
        raw_refresh, jti = self._token_service.create_refresh_token(user_id)

        expires_at = datetime.now(tz=timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
        )
        await self._refresh_token_repo.save(jti, user_id, expires_at, family_id)

        return TokenPairDTO(access_token=access_token, refresh_token=raw_refresh)

    @staticmethod
    def _to_profile_dto(user: User) -> UserProfileDTO:
        return UserProfileDTO(
            id=str(user.id().value),
            name=user.name().value,
            account=user.account().value,
            email=user.email().value if user.email() else None,
            phone=user.phone().value if user.phone() else None,
            bio=user.bio().value,
            is_active=user.is_active(),
            created_at=user.created_at(),
            updated_at=user.updated_at(),
            birth_date=user.birth_date().value if user.birth_date() is not None else None,
            career=user.career().value.value if user.career() is not None else None,
            tags=user.tags().value,
            avatar_url=user.avatar_url().value if user.avatar_url() is not None else None,
            language_skills=tuple(
                {"language": s.language, "proficiency": s.proficiency.value}
                for s in user.language_skills().value
            ),
            registered_address=user.registered_address(),
            residential_address=user.residential_address(),
            is_residential_same_as_registered=user.is_residential_same_as_registered(),
            gender=user.gender().value.value if user.gender() is not None else None,
            role=str(user.role().value.value) if hasattr(user.role(), "value") else str(user.role()),
        )

    async def admin_get_user(self, user_id: str) -> UserProfileDTO:
        """Admin: get any user's profile by ID."""
        user = await self._user_repo.find_by_id(UserId(uuid.UUID(user_id)))
        if user is None:
            raise ResourceNotFoundException(f"User '{user_id}' not found.", code="USER_NOT_FOUND")
        return self._to_profile_dto(user)

    async def admin_list_users(self, query: ListAllUsersQuery) -> PaginatedUsersDTO:
        """Admin: list all users with pagination and optional filters."""
        users, total = await self._user_repo.find_all(
            limit=query.limit,
            offset=query.offset,
            search=query.search,
            is_active=query.is_active,
        )
        return PaginatedUsersDTO(
            items=[self._to_profile_dto(u) for u in users],
            total=total,
            limit=query.limit,
            offset=query.offset,
        )

    async def admin_update_user(self, cmd: AdminUpdateUserCommand) -> UserProfileDTO:
        """Admin: update any user's profile."""
        now = datetime.now(tz=timezone.utc)
        user = await self._user_repo.find_by_id(UserId(uuid.UUID(cmd.user_id)))
        if user is None:
            raise ResourceNotFoundException(f"User '{cmd.user_id}' not found.", code="USER_NOT_FOUND")

        pf = cmd.provided_fields

        if "name" in pf and cmd.name is not None:
            user.update_name(UserName(cmd.name), now)
        if "bio" in pf and cmd.bio is not None:
            user.update_bio(cmd.bio, now)
        if "email" in pf:
            if cmd.email is not None:
                user.change_email(Email(cmd.email), now)
            else:
                user.clear_email(now)
        if "phone" in pf:
            if cmd.phone is not None:
                user.change_phone(Phone(cmd.phone), now)
            else:
                user.clear_phone(now)
        if "birth_date" in pf:
            user.update_birth_date(cmd.birth_date, now)
        if "career" in pf:
            user.update_career(cmd.career, now)
        if "tags" in pf:
            user.update_tags(list(cmd.tags), now)
        if "avatar_url" in pf:
            user.update_avatar_url(cmd.avatar_url, now)
        if "language_skills" in pf:
            user.update_language_skills(list(cmd.language_skills), now)
        if "registered_address" in pf:
            user.update_registered_address(cmd.registered_address, now)
        if "residential_address" in pf:
            user.update_residential_address(cmd.residential_address, now)
        if "is_residential_same_as_registered" in pf and cmd.is_residential_same_as_registered is not None:
            user.update_is_residential_same_as_registered(cmd.is_residential_same_as_registered, now)
        if "gender" in pf:
            user.update_gender(cmd.gender, now)
        if "is_active" in pf and cmd.is_active is not None:
            if cmd.is_active:
                user.activate(now)
            else:
                user.deactivate(now)
        if "role" in pf and cmd.role is not None:
            from app.domains.user.value_objects import UserRole
            user.update_role(UserRole(cmd.role), now)
        if "password" in pf and cmd.password is not None:
            hashed = self._password_hasher.hash(cmd.password)
            user.change_password(HashedPassword(hashed), now)

        await self._user_repo.save(user)
        logger.info("[admin] User updated by admin_id={}: user_id={}", cmd.admin_id, cmd.user_id)
        return self._to_profile_dto(user)
