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
                        is_selected=data.get("is_selected", False),
                        line_number=data.get("line_number"),
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
                    "is_selected": suggestion.is_selected,
                    "line_number": suggestion.line_number,
                })
            batch.commit()

    def select_suggestion(self, invoice_id: str, line_number: int, account_code: str) -> None:
        """
        Marca una sugerencia como seleccionada y desmarca las demás de esa línea.
        """
        # Desmarcar todas las sugerencias de esta línea
        all_for_line = self.suggestions_collection.where("invoice_id", "==", invoice_id).where("line_number", "==", line_number).get()
        batch = self.db.batch()
        for doc in all_for_line:
            batch.update(doc.reference, {"is_selected": False})
        batch.commit()
        
        # Marcar la seleccionada
        selected = self.suggestions_collection.where("invoice_id", "==", invoice_id).where("line_number", "==", line_number).where("account_code", "==", account_code).get()
        if selected:
            batch = self.db.batch()
            for doc in selected:
                batch.update(doc.reference, {"is_selected": True})
            batch.commit()