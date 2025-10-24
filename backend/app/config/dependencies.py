from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from app.application.use_cases import (
    AuthenticateUser,
    ExportInvoicesToExcel,
    GenerateAccountingSuggestions,
    GetInvoiceDetail,
    ListInvoices,
    RegisterUser,
    UploadInvoice,
)
from app.infrastructure import (
    BcryptPasswordHasher,
    FirebaseAdminUnavailable,
    InMemoryAISuggestionRepository,
    InMemoryInvoiceRepository,
    InMemoryUserRepository,
    JWTTokenService,
    OllamaAISuggestionService,
    SpreadsheetInvoiceWorkbookBuilder,
    UBLInvoiceParser,
    firebase_project_id,
    initialize_firebase_app,
)


@dataclass(slots=True)
class Settings:
    secret_key: str
    token_expire_minutes: int
    ai_base_url: str
    ai_model: str
    firebase_credentials_defined: bool


@lru_cache
def get_settings() -> Settings:
    firebase_credentials_defined = bool(
        os.getenv("FIREBASE_CREDENTIALS_PATH") or os.getenv("FIREBASE_CREDENTIALS_JSON")
    )
    return Settings(
        secret_key=os.getenv("SECRET_KEY", "insecure-development-secret"),
        token_expire_minutes=int(os.getenv("TOKEN_EXPIRE_MINUTES", "60")),
        ai_base_url=os.getenv("AI_BASE_URL", "http://ollama:11434"),
        ai_model=os.getenv("AI_MODEL", "phi3"),
        firebase_credentials_defined=firebase_credentials_defined,
    )


@lru_cache
def get_user_repository() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@lru_cache
def get_invoice_repository() -> InMemoryInvoiceRepository:
    return InMemoryInvoiceRepository()


@lru_cache
def get_ai_suggestion_repository() -> InMemoryAISuggestionRepository:
    return InMemoryAISuggestionRepository()


@lru_cache
def get_password_hasher() -> BcryptPasswordHasher:
    return BcryptPasswordHasher()


@lru_cache
def get_token_service() -> JWTTokenService:
    settings = get_settings()
    return JWTTokenService(
        secret_key=settings.secret_key,
        expires_minutes=settings.token_expire_minutes,
    )


@lru_cache
def get_invoice_parser() -> UBLInvoiceParser:
    return UBLInvoiceParser()


@lru_cache
def get_ai_suggestion_service() -> OllamaAISuggestionService:
    settings = get_settings()
    return OllamaAISuggestionService(
        base_url=settings.ai_base_url,
        model=settings.ai_model,
    )


@lru_cache
def get_invoice_workbook_builder() -> SpreadsheetInvoiceWorkbookBuilder:
    return SpreadsheetInvoiceWorkbookBuilder()


@lru_cache
def get_firebase_app():
    settings = get_settings()
    if not settings.firebase_credentials_defined:
        return None

    try:
        return initialize_firebase_app()
    except FirebaseAdminUnavailable:
        return None


@lru_cache
def get_firebase_project_id() -> str | None:
    settings = get_settings()
    if not settings.firebase_credentials_defined:
        return None

    try:
        return firebase_project_id()
    except FirebaseAdminUnavailable:
        return None


def get_register_user_use_case() -> RegisterUser:
    return RegisterUser(
        user_repository=get_user_repository(),
        password_hasher=get_password_hasher(),
    )


def get_authenticate_user_use_case() -> AuthenticateUser:
    return AuthenticateUser(
        user_repository=get_user_repository(),
        password_hasher=get_password_hasher(),
        token_service=get_token_service(),
    )


def get_upload_invoice_use_case() -> UploadInvoice:
    return UploadInvoice(
        invoice_repository=get_invoice_repository(),
        invoice_parser=get_invoice_parser(),
    )


def get_generate_accounting_suggestions_use_case() -> GenerateAccountingSuggestions:
    return GenerateAccountingSuggestions(
        invoice_repository=get_invoice_repository(),
        suggestion_repository=get_ai_suggestion_repository(),
        ai_service=get_ai_suggestion_service(),
    )


def get_export_invoices_use_case() -> ExportInvoicesToExcel:
    return ExportInvoicesToExcel(
        invoice_repository=get_invoice_repository(),
        suggestion_repository=get_ai_suggestion_repository(),
        workbook_builder=get_invoice_workbook_builder(),
    )


def get_list_invoices_use_case() -> ListInvoices:
    return ListInvoices(
        invoice_repository=get_invoice_repository(),
        suggestion_repository=get_ai_suggestion_repository(),
    )


def get_invoice_detail_use_case() -> GetInvoiceDetail:
    return GetInvoiceDetail(
        invoice_repository=get_invoice_repository(),
        suggestion_repository=get_ai_suggestion_repository(),
    )
