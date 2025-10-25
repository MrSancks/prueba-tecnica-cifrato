from typing import Protocol


class UserRepository(Protocol):
    def get_by_id(self, user_id: str) -> object | None:
        ...

    def get_by_email(self, email: str) -> object | None:
        ...

    def add(self, user: object) -> None:
        ...


class InvoiceRepository(Protocol):
    def get_by_id(self, invoice_id: str) -> object | None:
        ...

    def list_for_user(self, user_id: str) -> list[object]:
        ...

    def add(self, invoice: object) -> None:
        ...

    def find_by_owner_and_external_id(self, owner_id: str, external_id: str) -> object | None:
        ...


class AISuggestionRepository(Protocol):
    def list_for_invoice(self, invoice_id: str) -> list[object]:
        ...

    def replace_for_invoice(self, invoice_id: str, suggestions: list[object]) -> None:
        ...


class PUCRepository(Protocol):
    """Repositorio para gestionar cuentas PUC personalizadas por empresa"""
    
    def add(self, account: object) -> None:
        """Agrega una cuenta PUC"""
        ...

    def add_bulk(self, accounts: list[object]) -> None:
        """Agrega múltiples cuentas PUC en una transacción"""
        ...

    def list_by_owner(
        self, 
        owner_id: str, 
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[object], int]:
        """
        Lista cuentas PUC del owner con paginación y búsqueda.
        Returns: (lista_cuentas, total_count)
        """
        ...

    def get_by_owner_and_code(self, owner_id: str, codigo: str) -> object | None:
        """Obtiene una cuenta PUC específica por owner y código"""
        ...

    def delete_all_by_owner(self, owner_id: str) -> None:
        """Elimina todas las cuentas PUC de un owner (para reemplazo)"""
        ...

    def count_by_owner(self, owner_id: str) -> int:
        """Cuenta el total de cuentas PUC de un owner"""
        ...
