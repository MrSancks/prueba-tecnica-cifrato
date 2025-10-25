"""
Servicio para mapear códigos PUC de 4 dígitos a códigos específicos de 8 dígitos de la empresa.
"""
from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from pathlib import Path
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
    """
    
    def __init__(self, puc_file_path: str | None = None, api_key: str | None = None):
        self.accounts: list[PUCAccount] = []
        self.api_key = api_key
        self._initialized = False
        
        if puc_file_path:
            self.load_puc_from_csv(puc_file_path)
        
        if api_key and genai:
            try:
                genai.configure(api_key=api_key)
                self._initialized = True
                logger.info("✅ PUCMapperService inicializado con Gemini")
            except Exception as e:
                logger.error(f"❌ Error configurando Gemini para PUC Mapper: {e}")
    
    def load_puc_from_csv(self, file_path: str) -> None:
        """Carga el PUC desde un archivo CSV"""
        try:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"⚠️ Archivo PUC no encontrado: {file_path}")
                return
            
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Saltar filas de encabezado o vacías
                    if not row.get('Código') or row['Código'] == 'Código':
                        continue
                    
                    # Solo tomar cuentas transaccionales (nivel más bajo)
                    if row.get('Nivel agrupación') == 'Transaccional':
                        self.accounts.append(PUCAccount(
                            code=row['Código'].strip(),
                            name=row.get('Nombre', '').strip(),
                            category=row.get('Categoría', '').strip(),
                            class_type=row.get('Clase', '').strip(),
                            level=row.get('Nivel agrupación', '').strip(),
                        ))
            
            logger.info(f"✅ Cargadas {len(self.accounts)} cuentas del PUC desde {file_path}")
        except Exception as e:
            logger.error(f"❌ Error cargando PUC: {e}")
    
    def get_accounts_by_prefix(self, prefix: str) -> list[PUCAccount]:
        """Obtiene todas las cuentas que empiezan con el prefijo dado"""
        return [acc for acc in self.accounts if acc.code.startswith(prefix)]
    
    def map_to_specific_account(
        self,
        generic_code: str,
        description: str,
        rationale: str,
    ) -> dict[str, Any]:
        """
        Mapea un código PUC genérico (4 dígitos) a un código específico (8 dígitos)
        usando IA para analizar la descripción y encontrar la cuenta más apropiada.
        
        Returns:
            {
                "specific_code": "11050501",
                "account_name": "Efectivo CL 72",
                "confidence": 0.85,
                "explanation": "..."
            }
        """
        if not self._initialized or genai is None:
            # Fallback: devolver el primer código que coincida
            candidates = self.get_accounts_by_prefix(generic_code)
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
        candidates = self.get_accounts_by_prefix(generic_code)
        
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
            
            import json
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
