"""Service protocol definitions used by application use cases."""

from typing import Protocol


class PasswordHasher(Protocol):
    """Abstraction for hashing and verifying user passwords."""

    def hash(self, plain_password: str) -> str:
        """Transform a plaintext password into its hashed representation."""

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Validate that the plaintext password matches the stored hash."""


class TokenService(Protocol):
    """Abstraction for generating and verifying authentication tokens."""

    def create_access_token(self, subject: str) -> str:
        """Generate a token for the provided subject identifier."""

    def verify_token(self, token: str) -> dict[str, object]:
        """Validate the token and return its decoded payload."""


class AISuggestionService(Protocol):
    """Abstraction over the AI system that generates accounting suggestions."""

    def generate_suggestions(self, invoice_payload: dict[str, object]) -> list[dict[str, object]]:
        """Return AI-driven suggestions based on invoice data."""
