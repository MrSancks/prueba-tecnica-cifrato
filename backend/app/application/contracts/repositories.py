"""Repository protocol definitions used by application use cases."""

from typing import Protocol


class UserRepository(Protocol):
    """Persistence operations required for user aggregates."""

    def get_by_id(self, user_id: str) -> object | None:
        """Retrieve a user by its identifier."""

    def get_by_email(self, email: str) -> object | None:
        """Retrieve a user by email address."""

    def add(self, user: object) -> None:
        """Persist a new user entity."""


class InvoiceRepository(Protocol):
    """Persistence operations required for invoice aggregates."""

    def get_by_id(self, invoice_id: str) -> object | None:
        """Retrieve an invoice by its identifier."""

    def list_for_user(self, user_id: str) -> list[object]:
        """List invoices owned by a user."""

    def add(self, invoice: object) -> None:
        """Persist a new invoice entity."""
