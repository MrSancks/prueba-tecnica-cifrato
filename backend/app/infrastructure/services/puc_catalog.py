"""
Servicio para generar catálogo completo de cuentas PUC usando IA.
"""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
except ModuleNotFoundError:
    genai = None


class PUCCatalogGenerator:
    """
    Genera un catálogo completo de cuentas PUC usando Gemini AI.
    Toma los códigos seleccionados y genera toda la estructura jerárquica.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._initialized = False
        
        if genai and api_key:
            try:
                genai.configure(api_key=api_key)
                self._initialized = True
                logger.info("✅ PUCCatalogGenerator inicializado con Gemini")
            except Exception as e:
                logger.error(f"❌ Error configurando Gemini: {e}")
    
    def generate_catalog(
        self,
        selected_codes: list[str],
        suggestions_context: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Genera el catálogo completo de cuentas PUC incluyendo jerarquía.
        
        Args:
            selected_codes: Lista de códigos PUC seleccionados (8 dígitos)
            suggestions_context: Contexto de las sugerencias (rationale, invoice info)
        
        Returns:
            Lista de cuentas con estructura completa para Excel
        """
        if not self._initialized or not genai:
            logger.warning("Gemini no disponible, retornando estructura básica")
            return self._generate_basic_catalog(selected_codes)
        
        try:
            prompt = self._build_catalog_prompt(selected_codes, suggestions_context)
            
            logger.info(f"🤖 Generando catálogo PUC con Gemini para {len(selected_codes)} códigos")
            model = genai.GenerativeModel("gemini-2.5-flash-live")
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=8192,
                ),
            )
            
            text = response.text.strip()
            
            # Limpiar markdown
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            catalog = json.loads(text)
            
            if isinstance(catalog, dict) and "cuentas" in catalog:
                result = catalog["cuentas"]
            elif isinstance(catalog, list):
                result = catalog
            else:
                logger.warning("Formato inesperado de respuesta, usando fallback")
                return self._generate_basic_catalog(selected_codes)
            
            logger.info(f"✅ Catálogo generado: {len(result)} cuentas")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error generando catálogo con IA: {e}")
            return self._generate_basic_catalog(selected_codes)
    
    def _build_catalog_prompt(
        self,
        selected_codes: list[str],
        suggestions_context: list[dict[str, Any]],
    ) -> str:
        """
        Construye el prompt para que Gemini genere el catálogo completo.
        """
        context_lines = []
        for ctx in suggestions_context[:10]:  # Limitar a 10 para no exceder tokens
            context_lines.append(
                f"- {ctx.get('code', 'N/A')}: {ctx.get('rationale', 'N/A')}"
            )
        
        prompt = f"""Eres un experto contador colombiano. Genera un catálogo completo de cuentas PUC siguiendo el Plan Único de Cuentas colombiano.

CÓDIGOS SELECCIONADOS:
{', '.join(selected_codes)}

CONTEXTO DE USO:
{chr(10).join(context_lines)}

INSTRUCCIONES:
1. Para cada código, genera la estructura JERÁRQUICA completa (grupo, cuenta, subcuenta, auxiliar)
2. Usa nomenclatura estándar del PUC colombiano
3. Incluye todos los campos requeridos
4. Asegura que los nombres sean específicos y profesionales

RESPONDE SOLO CON JSON EN ESTE FORMATO:
[
  {{
    "codigo": "1",
    "nombre": "ACTIVO",
    "categoria": "Activos",
    "clase": "Activo",
    "relacion_con": "",
    "maneja_vencimientos": "No maneja vencimiento",
    "diferencia_fiscal": "No",
    "activo": "Sí",
    "nivel_agrupacion": "Clase"
  }},
  {{
    "codigo": "11",
    "nombre": "DISPONIBLE",
    "categoria": "Activos",
    "clase": "Activo Corriente",
    "relacion_con": "",
    "maneja_vencimientos": "No maneja vencimiento",
    "diferencia_fiscal": "No",
    "activo": "Sí",
    "nivel_agrupacion": "Grupo"
  }},
  {{
    "codigo": "1105",
    "nombre": "CAJA",
    "categoria": "Caja - Bancos",
    "clase": "Activo Corriente",
    "relacion_con": "Formas de pago",
    "maneja_vencimientos": "No maneja vencimiento",
    "diferencia_fiscal": "No",
    "activo": "Sí",
    "nivel_agrupacion": "Cuenta"
  }},
  {{
    "codigo": "110505",
    "nombre": "Caja general",
    "categoria": "Caja - Bancos",
    "clase": "Activo Corriente",
    "relacion_con": "Formas de pago",
    "maneja_vencimientos": "No maneja vencimiento",
    "diferencia_fiscal": "No",
    "activo": "Sí",
    "nivel_agrupacion": "Subcuenta"
  }},
  {{
    "codigo": "11050501",
    "nombre": "Efectivo caja principal",
    "categoria": "Caja - Bancos",
    "clase": "Activo Corriente",
    "relacion_con": "Formas de pago",
    "maneja_vencimientos": "No maneja vencimiento",
    "diferencia_fiscal": "No",
    "activo": "Sí",
    "nivel_agrupacion": "Transaccional"
  }}
]

Genera la jerarquía COMPLETA para TODOS los códigos seleccionados."""
        
        return prompt
    
    def _generate_basic_catalog(self, selected_codes: list[str]) -> list[dict[str, Any]]:
        """
        Genera un catálogo básico sin IA (fallback).
        """
        catalog = []
        for code in selected_codes:
            catalog.append({
                "codigo": code,
                "nombre": f"Cuenta {code}",
                "categoria": self._get_basic_category(code),
                "clase": self._get_basic_class(code),
                "relacion_con": "Formas de pago",
                "maneja_vencimientos": "No maneja vencimiento",
                "diferencia_fiscal": "No",
                "activo": "Sí" if code.startswith("1") else "No",
                "nivel_agrupacion": "Transaccional",
            })
        return catalog
    
    def _get_basic_category(self, code: str) -> str:
        """Categoría básica según primer dígito"""
        if code.startswith("1"):
            return "Activos"
        elif code.startswith("2"):
            return "Pasivos"
        elif code.startswith("3"):
            return "Patrimonio"
        elif code.startswith("4"):
            return "Ingresos"
        elif code.startswith("5"):
            return "Gastos"
        elif code.startswith("6"):
            return "Costos"
        return "Otros"
    
    def _get_basic_class(self, code: str) -> str:
        """Clase básica según código"""
        if code.startswith("1"):
            return "Activo Corriente"
        elif code.startswith("2"):
            return "Pasivo Corriente"
        elif code.startswith("4"):
            return "Ingresos Operacionales"
        elif code.startswith("5"):
            return "Gastos Operacionales"
        elif code.startswith("6"):
            return "Costos"
        return "Otros"
