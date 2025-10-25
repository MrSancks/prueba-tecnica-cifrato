"""
Servicio para mapear códigos PUC de 4 dígitos a códigos específicos de 8 dígitos de la empresa.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
except ModuleNotFoundError:
    genai = None


@dataclass
class PUCAccount:
    """Cuenta del PUC de la empresa"""
    code: str  # Código completo (ej: "11050501")
    name: str  # Nombre de la cuenta
    category: str  # Categoría
    class_type: str  # Clase
    level: str  # Nivel de agrupación


class PUCMapperService:
    """
    Servicio que mapea códigos PUC genéricos (4 dígitos) a códigos específicos
    de la empresa (8 dígitos) usando IA.
    
    Ahora carga las cuentas desde el repositorio en lugar de un archivo CSV.
    """
    
    def __init__(self, puc_repository=None, api_key: str | None = None):
        self.puc_repository = puc_repository
        self.api_key = api_key
        self._initialized = False
        
        if api_key and genai:
            try:
                genai.configure(api_key=api_key)
                self._initialized = True
                logger.info("✅ PUCMapperService inicializado con Gemini")
            except Exception as e:
                logger.error(f"❌ Error configurando Gemini para PUC Mapper: {e}")
    
    def load_accounts_for_owner(self, owner_id: str) -> list[PUCAccount]:
        """
        Carga las cuentas PUC del owner desde el repositorio.
        
        Returns:
            Lista de PUCAccount con las cuentas del owner
        """
        if not self.puc_repository:
            logger.warning("⚠️ No hay repositorio PUC configurado")
            return []
        
        try:
            # Obtener todas las cuentas del owner (sin paginación)
            accounts_domain, _ = self.puc_repository.list_by_owner(
                owner_id=owner_id,
                search=None,
                limit=10000,
                offset=0,
            )
            
            # Convertir a formato interno
            accounts = []
            for acc in accounts_domain:
                # Solo tomar cuentas transaccionales
                if acc.nivel_agrupacion.lower() == "transaccional":
                    accounts.append(PUCAccount(
                        code=acc.codigo,
                        name=acc.nombre,
                        category=acc.categoria,
                        class_type=acc.clase,
                        level=acc.nivel_agrupacion,
                    ))
            
            logger.info(f"✅ Cargadas {len(accounts)} cuentas PUC para owner {owner_id}")
            return accounts
            
        except Exception as e:
            logger.error(f"❌ Error cargando PUC para owner {owner_id}: {e}")
            return []
    
    def get_accounts_by_prefix(self, accounts: list[PUCAccount], prefix: str) -> list[PUCAccount]:
        """Obtiene todas las cuentas que empiezan con el prefijo dado"""
        return [acc for acc in accounts if acc.code.startswith(prefix)]
    
    def map_to_specific_account(
        self,
        owner_id: str,
        generic_code: str,
        description: str,
        rationale: str,
    ) -> dict[str, Any]:
        """
        Mapea un código PUC genérico (4 dígitos) a un código específico (8 dígitos)
        usando IA para analizar la descripción y encontrar la cuenta más apropiada.
        
        Args:
            owner_id: ID del propietario/empresa
            generic_code: Código PUC genérico (4 dígitos)
            description: Descripción de la transacción
            rationale: Justificación del mapeo
        
        Returns:
            {
                "specific_code": "11050501",
                "account_name": "Efectivo CL 72",
                "confidence": 0.85,
                "explanation": "..."
            }
        """
        # Cargar cuentas del owner
        accounts = self.load_accounts_for_owner(owner_id)
        
        if not accounts:
            logger.warning(f"⚠️ Owner {owner_id} no tiene PUC cargado")
            return {
                "specific_code": generic_code,
                "account_name": "Cuenta genérica (sin PUC personalizado)",
                "confidence": 0.3,
                "explanation": "El usuario no ha cargado un PUC personalizado",
            }
        
        if not self._initialized or genai is None:
            # Fallback: devolver el primer código que coincida
            candidates = self.get_accounts_by_prefix(accounts, generic_code)
            if candidates:
                return {
                    "specific_code": candidates[0].code,
                    "account_name": candidates[0].name,
                    "confidence": 0.5,
                    "explanation": f"Selección automática sin IA: {candidates[0].name}",
                }
            return {
                "specific_code": generic_code,
                "account_name": "Cuenta genérica",
                "confidence": 0.3,
                "explanation": "No se encontró cuenta específica",
            }
        
        # Obtener candidatos que empiecen con el código genérico
        candidates = self.get_accounts_by_prefix(accounts, generic_code)
        
        if not candidates:
            return {
                "specific_code": generic_code,
                "account_name": "Cuenta genérica",
                "confidence": 0.3,
                "explanation": "No hay cuentas específicas disponibles",
            }
        
        if len(candidates) == 1:
            # Solo hay una opción
            return {
                "specific_code": candidates[0].code,
                "account_name": candidates[0].name,
                "confidence": 0.9,
                "explanation": f"Única cuenta disponible: {candidates[0].name}",
            }
        
        # Usar IA para seleccionar la más apropiada
        try:
            prompt = self._build_mapping_prompt(generic_code, description, rationale, candidates)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=512,
                ),
            )
            
            text = response.text.strip()
            
            # Limpiar markdown si existe
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            result = json.loads(text)
            
            return {
                "specific_code": result.get("code", candidates[0].code),
                "account_name": result.get("name", candidates[0].name),
                "confidence": result.get("confidence", 0.7),
                "explanation": result.get("explanation", "Selección por IA"),
            }
        
        except Exception as e:
            logger.error(f"❌ Error en mapeo con IA: {e}")
            # Fallback: devolver la primera
            return {
                "specific_code": candidates[0].code,
                "account_name": candidates[0].name,
                "confidence": 0.5,
                "explanation": f"Error en IA, usando: {candidates[0].name}",
            }
    
    def _build_mapping_prompt(
        self,
        generic_code: str,
        description: str,
        rationale: str,
        candidates: list[PUCAccount],
    ) -> str:
        """Construye el prompt para que IA seleccione la cuenta específica"""
        prompt_lines = [
            "Eres un experto contador. Selecciona la cuenta PUC MÁS APROPIADA para esta transacción.",
            "",
            f"CÓDIGO GENÉRICO: {generic_code}",
            f"DESCRIPCIÓN: {description}",
            f"JUSTIFICACIÓN: {rationale}",
            "",
            "CUENTAS DISPONIBLES:",
        ]
        
        for idx, acc in enumerate(candidates[:20], 1):  # Limitar a 20 para no exceder tokens
            prompt_lines.append(f"{idx}. {acc.code} - {acc.name} ({acc.category})")
        
        prompt_lines.extend([
            "",
            "RESPONDE SOLO CON JSON:",
            '{',
            '  "code": "11050501",',
            '  "name": "Efectivo CL 72",',
            '  "confidence": 0.95,',
            '  "explanation": "Razón de la selección"',
            '}',
        ])
        
        return "\n".join(prompt_lines)
