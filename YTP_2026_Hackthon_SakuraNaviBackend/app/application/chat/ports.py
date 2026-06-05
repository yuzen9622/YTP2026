"""Port (Protocol) interfaces for chat infrastructure."""
from typing import AsyncGenerator, Protocol, runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    """Async streaming LLM client protocol."""

    async def stream_chat(
        self,
        messages: list[dict],
        tools: list[dict],
    ) -> AsyncGenerator[dict, None]:
        """Send chat request and yield parsed SSE events.

        Args:
            messages: OpenAI-compatible message list.
            tools: OpenAI-compatible tool definitions.

        Yields:
            Parsed event dicts from the SSE stream (delta, tool_calls, etc.).
        """
        ...

    async def close(self) -> None:
        """Release underlying resources held by the client."""
        ...


@runtime_checkable
class ToolExecutor(Protocol):
    """Tool execution protocol."""

    async def execute(
        self,
        tool_name: str,
        arguments: str,
        user_id: str,
        conversation_id: str | None = None,
    ) -> dict:
        """Execute a tool and return its result.

        Args:
            tool_name: Name of the tool to execute.
            arguments: JSON string of tool arguments.
            user_id: Authenticated user ID for context.
            conversation_id: Optional conversation scope for tools that need
                per-conversation isolation (e.g. resume draft workflow).

        Returns:
            Tool result dict (JSON-serializable).
        """
        ...

    async def close(self) -> None:
        """Release any resources held by the executor."""
        ...

    def get_tool_definitions(self) -> list[dict]:
        """Return the list of LLM-compatible tool definitions.

        Exposes infrastructure-level tool metadata through the port so the
        application service does not need to import from the infrastructure layer.
        """
        ...
