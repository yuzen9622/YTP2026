"""Query objects for read operations."""
from dataclasses import dataclass


@dataclass(frozen=True)
class GetUserProfileQuery:
    """Query to retrieve a user's profile by user_id."""
    user_id: str
