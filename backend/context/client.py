from typing import Protocol, runtime_checkable


@runtime_checkable
class AIClient(Protocol):
    """Completion client protocol — enables test injection without importing anthropic."""
    model: str

    def complete(
        self,
        system: str,
        user_prompt: str,
        max_tokens: int = 4096,
    ) -> tuple[str, int, int]:
        """Returns (response_text, input_token_count, output_token_count)."""
        ...


class ClaudeClient:
    """Thin wrapper around the Anthropic Messages API."""

    def __init__(self, api_key: str, model: str = "claude-opus-4-7") -> None:
        # Lazy import keeps startup fast when key is absent
        import anthropic
        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def complete(
        self,
        system: str,
        user_prompt: str,
        max_tokens: int = 4096,
    ) -> tuple[str, int, int]:
        msg = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return msg.content[0].text, msg.usage.input_tokens, msg.usage.output_tokens
