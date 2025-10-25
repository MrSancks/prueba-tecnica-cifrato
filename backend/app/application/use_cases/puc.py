"""
Casos de uso para gestión de PUC (Plan Único de Cuentas) personalizado.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from app.application.contracts.repositories import PUCRepository
from app.domain.puc import PUCAccount

logger = logging.getLogger(__name__)


class PUCUploadError(Exception):
    """Error al subir archivo PUC"""


@dataclass
class UploadPUC:
    """Caso de uso: Subir archivo Excel con PUC personalizado"""
    
    puc_repository: PUCRepository
    excel_parser: object  # PUCExcelParserService
    
    def execute(self, owner_id: str, file_content: bytes, filename: str) -> dict:
        """
        Procesa un archivo Excel con PUC y lo guarda en el repositorio.
        Reemplaza cualquier PUC existente del mismo owner.
        
        Returns:
            {
                "total_cuentas": 150,
                "mensaje": "PUC cargado exitosamente"
            }
        """
        try:
            # Validar extensión del archivo
            if not filename.lower().endswith((".xlsx", ".xls")):
                raise PUCUploadError("El archivo debe ser formato Excel (.xlsx o .xls)")
            
            # Parsear el archivo Excel (detecta automáticamente .xlsx o .xls)
            logger.info(f"📊 Parseando archivo Excel: {filename}")
            accounts = self.excel_parser.parse_excel(file_content, owner_id, filename)
            
            if not accounts:
                raise PUCUploadError("No se encontraron cuentas válidas en el archivo")
            
            # Eliminar PUC anterior del mismo owner
            logger.info(f"🗑️ Eliminando PUC anterior del owner {owner_id}")
            self.puc_repository.delete_all_by_owner(owner_id)
            
            # Guardar nuevo PUC
            logger.info(f"💾 Guardando {len(accounts)} cuentas PUC")
            self.puc_repository.add_bulk(accounts)
            
            logger.info(f"✅ PUC cargado exitosamente: {len(accounts)} cuentas")
            return {
                "total_cuentas": len(accounts),
                "mensaje": f"PUC cargado exitosamente con {len(accounts)} cuentas",
            }
            
        except PUCUploadError:
            raise
        except Exception as e:
            logger.error(f"❌ Error subiendo PUC: {e}")
            raise PUCUploadError(f"Error procesando archivo: {str(e)}") from e


@dataclass
class ListPUC:
    """Caso de uso: Listar cuentas PUC con paginación y búsqueda"""
    
    puc_repository: PUCRepository
    
    def execute(
        self, 
        owner_id: str, 
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """
        Lista cuentas PUC del owner con paginación y búsqueda.
        
        Returns:
            {
                "cuentas": [...],
                "total": 150,
                "page": 1,
                "page_size": 50,
                "total_pages": 3
            }
        """
        # Calcular offset
        offset = (page - 1) * page_size
        
        # Obtener cuentas paginadas
        accounts, total = self.puc_repository.list_by_owner(
            owner_id=owner_id,
            search=search,
            limit=page_size,
            offset=offset,
        )
        
        # Calcular total de páginas
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return {
            "cuentas": accounts,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }


@dataclass
class GetPUCStats:
    """Caso de uso: Obtener estadísticas del PUC del usuario"""
    
    puc_repository: PUCRepository
    
    def execute(self, owner_id: str) -> dict:
        """
        Obtiene estadísticas básicas del PUC del owner.
        
        Returns:
            {
                "total_cuentas": 150,
                "tiene_puc": True
            }
        """
        total = self.puc_repository.count_by_owner(owner_id)
        
        return {
            "total_cuentas": total,
            "tiene_puc": total > 0,
        }


@dataclass
class GetPUCForAI:
    """Caso de uso: Obtener PUC en formato JSON para enviar a la IA"""
    
    puc_repository: PUCRepository
    
    def execute(self, owner_id: str) -> list[dict]:
        """
        Obtiene todas las cuentas PUC del owner en formato JSON
        para ser usado como contexto en prompts de IA.
        
        Returns:
            [
                {
                    "codigo": "11050501",
                    "nombre": "Efectivo CL 72",
                    "categoria": "Caja - Bancos",
                    "clase": "Activo",
                    ...
                },
                ...
            ]
        """
        # Obtener todas las cuentas (sin paginación para la IA)
        accounts, _ = self.puc_repository.list_by_owner(
            owner_id=owner_id,
            search=None,
            limit=10000,  # Límite alto para obtener todas
            offset=0,
        )
        
        # Convertir a diccionarios simples
        return [
            {
                "codigo": acc.codigo,
                "nombre": acc.nombre,
                "categoria": acc.categoria,
                "clase": acc.clase,
                "relacion_con": acc.relacion_con,
                "maneja_vencimientos": acc.maneja_vencimientos,
                "diferencia_fiscal": acc.diferencia_fiscal,
                "activo": acc.activo,
                "nivel_agrupacion": acc.nivel_agrupacion,
            }
            for acc in accounts
        ]
