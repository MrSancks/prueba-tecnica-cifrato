from __future__ import annotations

import logging
from typing import List

from firebase_admin import firestore

from app.domain.ai import AISuggestion
from app.application.contracts.repositories import AISuggestionRepository
from app.infrastructure.services.firebase_admin import initialize_firebase_app

logger = logging.getLogger(__name__)

class FirestoreAISuggestionRepository(AISuggestionRepository):
    def __init__(self) -> None:
        try:
            app = initialize_firebase_app()
            self.db = firestore.client(app)
            self.suggestions_collection = self.db.collection('suggestions')
            logger.info("Successfully connected to Firestore - Suggestions Collection")
        except Exception as e:
            logger.error(f"Error connecting to Firestore: {e}")
            raise

    def list_for_invoice(self, invoice_id: str) -> List[AISuggestion]:
        query = self.suggestions_collection.where("invoice_id", "==", invoice_id).get()
        result = []
        for doc in query:
            data = doc.to_dict()
            if data:
                result.append(
                    AISuggestion(
                        account_code=data.get("account_code"),
                        rationale=data.get("rationale"),
                        confidence=data.get("confidence"),
                        source=data.get("source") or "unknown",
                        generated_at=data.get("generated_at"),
                        line_number=data.get("line_number"),
                        puc_account_id=data.get("puc_account_id"),
                        account_name=data.get("account_name"),
                    )
                )
        return result

    def replace_for_invoice(self, invoice_id: str, suggestions: List[AISuggestion]) -> None:
        # Delete existing suggestions for this invoice
        existing_docs = self.suggestions_collection.where("invoice_id", "==", invoice_id).get()
        batch = self.db.batch()
        for doc in existing_docs:
            batch.delete(doc.reference)
        batch.commit()
        
        # Add new suggestions
        if suggestions:
            batch = self.db.batch()
            for suggestion in suggestions:
                doc_ref = self.suggestions_collection.document()
                batch.set(doc_ref, {
                    "invoice_id": invoice_id,
                    "account_code": suggestion.account_code,
                    "rationale": suggestion.rationale,
                    "confidence": suggestion.confidence,
                    "source": suggestion.source,
                    "generated_at": suggestion.generated_at,
                    "line_number": suggestion.line_number,
                    "puc_account_id": suggestion.puc_account_id,
                    "account_name": suggestion.account_name,
                })
            batch.commit()