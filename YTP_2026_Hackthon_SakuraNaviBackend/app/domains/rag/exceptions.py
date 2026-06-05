"""RAG domain exceptions."""


class RagDocumentNotFoundException(Exception):
    """Raised when a RagDocument cannot be located."""
    def __init__(self, message: str = "RAG document not found.") -> None:
        self.message = message
        super().__init__(self.message)


class RagIngestionException(Exception):
    """Raised when document ingestion (parsing/chunking/embedding) fails."""
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)
