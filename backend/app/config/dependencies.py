from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from functools import lru_cache

logger = logging.getLogger(__name__)

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
    JWTTokenService,
    GeminiAISuggestionService,
    SpreadsheetInvoiceWorkbookBuilder,
    UBLInvoiceParser,
    firebase_project_id,
    initialize_firebase_app,
)
from app.infrastructure.repositories.firestore_users import FirestoreUserRepository
from app.infrastructure.repositories.firestore_invoices import FirestoreInvoiceRepository
from app.infrastructure.repositories.firestore_suggestions import FirestoreAISuggestionRepository


@dataclass(slots=True)
class Settings:
    secret_key: str
    token_expire_minutes: int
    firebase_credentials_defined: bool
    gemini_api_key: str | None


@lru_cache
def get_settings() -> Settings:
    # Use only FIREBASE_CREDENTIALS_JSON; do not consider FIREBASE_CREDENTIALS_PATH
    firebase_credentials_defined = bool(os.getenv("FIREBASE_CREDENTIALS_JSON"))
    
    return Settings(
        secret_key=os.getenv("SECRET_KEY", "insecure-development-secret"),
        token_expire_minutes=int(os.getenv("TOKEN_EXPIRE_MINUTES", "60")),
        firebase_credentials_defined=firebase_credentials_defined,
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
    )


@lru_cache
def get_user_repository() -> FirestoreUserRepository:
    return FirestoreUserRepository()


@lru_cache
def get_invoice_repository() -> FirestoreInvoiceRepository:
    return FirestoreInvoiceRepository()


@lru_cache
def get_ai_suggestion_repository() -> FirestoreAISuggestionRepository:
    return FirestoreAISuggestionRepository()


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
def get_ai_suggestion_service() -> GeminiAISuggestionService:
    """
    Factory que retorna el servicio de AI Gemini.
    Requiere GEMINI_API_KEY en el entorno.
    """
    settings = get_settings()
    
    api_key = settings.gemini_api_key
    
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY no está configurado en las variables de entorno"
        )
    
    return GeminiAISuggestionService(api_key=api_key)


@lru_cache
def get_invoice_workbook_builder() -> SpreadsheetInvoiceWorkbookBuilder:
    settings = get_settings()
    
    # Crear generador de catálogo PUC si hay API key
    puc_generator = None
    if settings.gemini_api_key:
        try:
            from app.infrastructure.services.puc_catalog import PUCCatalogGenerator
            puc_generator = PUCCatalogGenerator(api_key=settings.gemini_api_key)
        except Exception as e:
            logger.warning(f"No se pudo inicializar PUCCatalogGenerator: {e}")
    
    return SpreadsheetInvoiceWorkbookBuilder(puc_catalog_generator=puc_generator)


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
