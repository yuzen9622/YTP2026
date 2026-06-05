"""Admin domain value objects."""
import enum
import uuid
from dataclasses import dataclass


class AdminRole(str, enum.Enum):
    """Admin job role."""
    SUPERADMIN = "superadmin"
    CUSTOMER_SERVICE = "customer_service"
    SECURITY_REVIEWER = "security_reviewer"
    CONTENT_MANAGER = "content_manager"


@dataclass(frozen=True)
class AdminId:
    """Admin entity unique identifier."""
    value: uuid.UUID

    def __post_init__(self):
        if not isinstance(self.value, uuid.UUID):
            raise ValueError(f"Invalid AdminId: {self.value}")
