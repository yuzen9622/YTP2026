"""Resume domain exceptions."""


class ResumeNotFoundException(Exception):
    """Raised when a resume is not found."""
    def __init__(self, message: str = "Resume not found.") -> None:
        self.message = message
        super().__init__(self.message)


class ResumeAccessDeniedException(Exception):
    """Raised when a user tries to access another user's resume."""
    def __init__(self, message: str = "You do not have permission to access this resume.") -> None:
        self.message = message
        super().__init__(self.message)
