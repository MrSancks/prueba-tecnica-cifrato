"""
Implementación del repositorio de PUC usando Firestore.
"""
from __future__ import annotations

import logging
from typing import Any

from app.domain.puc import PUCAccount

logger = logging.getLogger(__name__)


class FirestorePUCRepository:
    """Repositorio de cuentas PUC usando Firestore"""
    
    def __init__(self, firestore_client):
        self.db = firestore_client
        self.collection_name = "puc_accounts"
    
    def add(self, account: PUCAccount) -> None:
        """Agrega una cuenta PUC"""
        doc_ref = self.db.collection(self.collection_name).document(account.id)
        doc_ref.set(self._to_dict(account))
        logger.info(f"✅ Cuenta PUC guardada: {account.codigo} - {account.nombre}")
    
    def add_bulk(self, accounts: list[PUCAccount]) -> None:
        """Agrega múltiples cuentas PUC en lotes"""
        if not accounts:
            return
        
        batch = self.db.batch()
        count = 0
        
        for account in accounts:
            doc_ref = self.db.collection(self.collection_name).document(account.id)
            batch.set(doc_ref, self._to_dict(account))
            count += 1
            
            # Firestore permite máximo 500 operaciones por batch
            if count >= 500:
                batch.commit()
                batch = self.db.batch()
                count = 0
        
        if count > 0:
            batch.commit()
        
        logger.info(f"✅ {len(accounts)} cuentas PUC guardadas en lote")
    
    def list_by_owner(
        self, 
        owner_id: str, 
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[PUCAccount], int]:
        """Lista cuentas PUC del owner con paginación y búsqueda"""
        query = self.db.collection(self.collection_name).where("owner_id", "==", owner_id)
        
        # Obtener todos los documentos para hacer búsqueda local (Firestore tiene limitaciones en búsqueda de texto)
        all_docs = list(query.stream())
        
        # Filtrar por búsqueda si se proporciona
        if search and search.strip():
            search_lower = search.lower().strip()
            filtered_docs = [
                doc for doc in all_docs
                if self._matches_search(doc.to_dict(), search_lower)
            ]
        else:
            filtered_docs = all_docs
        
        total_count = len(filtered_docs)
        
        # Aplicar paginación
        paginated_docs = filtered_docs[offset:offset + limit]
        
        accounts = [self._from_dict(doc.id, doc.to_dict()) for doc in paginated_docs]
        
        return accounts, total_count
    
    def get_by_owner_and_code(self, owner_id: str, codigo: str) -> PUCAccount | None:
        """Obtiene una cuenta PUC específica por owner y código"""
        query = (
            self.db.collection(self.collection_name)
            .where("owner_id", "==", owner_id)
            .where("codigo", "==", codigo)
            .limit(1)
        )
        
        docs = list(query.stream())
        if not docs:
            return None
        
        doc = docs[0]
        return self._from_dict(doc.id, doc.to_dict())
    
    def delete_all_by_owner(self, owner_id: str) -> None:
        """Elimina todas las cuentas PUC de un owner"""
        query = self.db.collection(self.collection_name).where("owner_id", "==", owner_id)
        docs = list(query.stream())
        
        if not docs:
            return
        
        batch = self.db.batch()
        count = 0
        
        for doc in docs:
            batch.delete(doc.reference)
            count += 1
            
            if count >= 500:
                batch.commit()
                batch = self.db.batch()
                count = 0
        
        if count > 0:
            batch.commit()
        
        logger.info(f"✅ {len(docs)} cuentas PUC eliminadas para owner {owner_id}")
    
    def count_by_owner(self, owner_id: str) -> int:
        """Cuenta el total de cuentas PUC de un owner"""
        query = self.db.collection(self.collection_name).where("owner_id", "==", owner_id)
        docs = list(query.stream())
        return len(docs)
    
    def _to_dict(self, account: PUCAccount) -> dict[str, Any]:
        """Convierte entidad a diccionario para Firestore"""
        return {
            "owner_id": account.owner_id,
            "codigo": account.codigo,
            "nombre": account.nombre,
            "categoria": account.categoria,
            "clase": account.clase,
            "relacion_con": account.relacion_con,
            "maneja_vencimientos": account.maneja_vencimientos,
            "diferencia_fiscal": account.diferencia_fiscal,
            "activo": account.activo,
            "nivel_agrupacion": account.nivel_agrupacion,
            "created_at": account.created_at,
        }
    
    def _from_dict(self, doc_id: str, data: dict[str, Any]) -> PUCAccount:
        """Convierte diccionario de Firestore a entidad"""
        return PUCAccount(
            id=doc_id,
            owner_id=data["owner_id"],
            codigo=data["codigo"],
            nombre=data["nombre"],
            categoria=data.get("categoria", ""),
            clase=data.get("clase", ""),
            relacion_con=data.get("relacion_con", ""),
            maneja_vencimientos=data.get("maneja_vencimientos", ""),
            diferencia_fiscal=data.get("diferencia_fiscal", ""),
            activo=data.get("activo", ""),
            nivel_agrupacion=data.get("nivel_agrupacion", ""),
            created_at=data["created_at"],
        )
    
    def _matches_search(self, data: dict[str, Any], search_term: str) -> bool:
        """Verifica si un documento coincide con el término de búsqueda"""
        searchable_fields = [
            data.get("codigo", ""),
            data.get("nombre", ""),
            data.get("categoria", ""),
            data.get("clase", ""),
            data.get("relacion_con", ""),
        ]
        
        combined_text = " ".join(str(field).lower() for field in searchable_fields)
        return search_term in combined_text
