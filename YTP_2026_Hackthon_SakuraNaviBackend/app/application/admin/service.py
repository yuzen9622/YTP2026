"""Application service for admin-related use cases."""
import uuid
from datetime import datetime, timezone

from app.application.admin.commands import (
    AuthenticateAdminCommand,
    RegisterAdminCommand,
    RemoveAdminCommand,
    UpdateAdminCommand,
)
from app.application.admin.dtos import AdminAuthDTO, AdminDTO, AdminListDTO
from app.domains.admin.entity import Admin
from app.domains.admin.exceptions import (
    AdminAlreadyExistsException,
    AdminNotFoundException,
    InvalidAdminCredentialsException,
)
from app.domains.admin.repository import AdminRepository
from app.domains.admin.value_objects import AdminId, AdminRole
from app.infrastructure.auth.admin_jwt_service import AdminJwtService
from app.infrastructure.auth.password_service import BcryptPasswordHasher


class AdminApplicationService:
    """Application service orchestrating admin-related use cases."""

    def __init__(
        self,
        admin_repo: AdminRepository,
        password_hasher: BcryptPasswordHasher,
        jwt_service: AdminJwtService,
    ) -> None:
        self._admin_repo = admin_repo
        self._password_hasher = password_hasher
        self._jwt_service = jwt_service

    async def register_admin(self, cmd: RegisterAdminCommand) -> AdminDTO:
        """Register a new standalone admin account."""
        if await self._admin_repo.exists_by_account(cmd.account):
            raise AdminAlreadyExistsException(
                f"Admin account '{cmd.account}' already exists."
            )
        now = datetime.now(tz=timezone.utc)
        hashed = self._password_hasher.hash(cmd.password)
        admin = Admin(
            id=AdminId(uuid.uuid4()),
            account=cmd.account,
            hashed_password=hashed,
            role=AdminRole(cmd.role),
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        await self._admin_repo.save(admin)
        return self._to_dto(admin)

    async def authenticate_admin(self, cmd: AuthenticateAdminCommand) -> AdminAuthDTO:
        """Authenticate admin with account + password. Returns token."""
        admin = await self._admin_repo.find_by_account(cmd.account)

        # Always run bcrypt regardless of whether the account exists.
        # This prevents timing-based account enumeration: an attacker cannot
        # distinguish "account not found" from "wrong password" by measuring
        # response latency.
        check_hash = (
            admin.hashed_password()
            if admin is not None
            else self._password_hasher.dummy_hash
        )
        password_ok = self._password_hasher.verify(cmd.password, check_hash)

        if not password_ok or admin is None:
            raise InvalidAdminCredentialsException("Invalid account or password.")
        if not admin.is_active():
            raise InvalidAdminCredentialsException("Admin account is deactivated.")
        token = self._jwt_service.create_admin_access_token(
            str(admin.id().value), admin.role().value
        )
        return AdminAuthDTO(
            id=str(admin.id().value),
            account=admin.account(),
            role=admin.role().value,
            access_token=token,
        )

    async def list_admins(self, limit: int = 20, offset: int = 0) -> AdminListDTO:
        """List all active admins with pagination."""
        admins, total = await self._admin_repo.find_all(limit=limit, offset=offset, is_active=True)
        return AdminListDTO(
            items=[self._to_dto(a) for a in admins],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_admin_by_id(self, admin_id: str) -> AdminDTO:
        """Get admin by admin_id. Raises if not found."""
        admin = await self._admin_repo.find_by_id(AdminId(uuid.UUID(admin_id)))
        if admin is None:
            raise AdminNotFoundException(f"Admin not found: '{admin_id}'.")
        return self._to_dto(admin)

    async def update_admin(self, cmd: UpdateAdminCommand) -> AdminDTO:
        """Update an admin's role, active status, or password."""
        admin = await self._admin_repo.find_by_id(AdminId(uuid.UUID(cmd.admin_id)))
        if admin is None:
            raise AdminNotFoundException(f"Admin not found: '{cmd.admin_id}'.")
        now = datetime.now(tz=timezone.utc)
        if cmd.role is not None:
            admin.update_role(AdminRole(cmd.role), now)
        if cmd.is_active is not None:
            if cmd.is_active:
                admin.activate(now)
            else:
                admin.deactivate(now)
        if cmd.new_password is not None:
            admin.change_password(self._password_hasher.hash(cmd.new_password), now)
        await self._admin_repo.save(admin)
        return self._to_dto(admin)

    async def remove_admin(self, cmd: RemoveAdminCommand) -> None:
        """Remove admin by deactivating them."""
        admin = await self._admin_repo.find_by_id(AdminId(uuid.UUID(cmd.admin_id)))
        if admin is None:
            raise AdminNotFoundException(f"Admin not found: '{cmd.admin_id}'.")
        now = datetime.now(tz=timezone.utc)
        admin.deactivate(now)
        await self._admin_repo.save(admin)

    @staticmethod
    def _to_dto(admin: Admin) -> AdminDTO:
        return AdminDTO(
            id=str(admin.id().value),
            account=admin.account(),
            role=admin.role().value,
            is_active=admin.is_active(),
            created_at=admin.created_at(),
            updated_at=admin.updated_at(),
        )