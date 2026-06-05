"""Domain events for user aggregate."""
import dataclasses
from datetime import datetime

from app.domains.user.value_objects import UserId


@dataclasses.dataclass(frozen=True)
class UserRegisteredEvent:
    """Event fired when a new user registers."""
    user_id: UserId
    account: str
    occurred_at: datetime = dataclasses.field(default_factory=datetime.now)


@dataclasses.dataclass(frozen=True)
class UserLoggedInEvent:
    """Event fired when a user successfully logs in."""
    user_id: UserId
    occurred_at: datetime = dataclasses.field(default_factory=datetime.now)
