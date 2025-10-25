from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Any
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
except ModuleNotFoundError:
    genai = None  # type: ignore[assignment]


@dataclass(slots=True)
class GeminiAISuggestionService:
    """
    Servicio de sugerencias contables usando Google Generative AI (Gemini).
    - Modelo por defecto: gemini-2.5-flash
    - Requiere variable de entorno GEMINI_API_KEY (o pasar api_key)
    - Usa el PUC personalizado del repositorio por owner_id
    - Devuelve: list[dict[str, object]] con campos sugeridos por línea
    """
    api_key: str
    puc_repository: Any = None  # PUCRepository
    model_name: str = "gemini-2.5-flash"
    _initialized: bool = False

    def __post_init__(self) -> None:
        if genai is None or not self.api_key:
            # SDK no instalado o no hay API key → no inicializa
            logger.warning("GeminiAISuggestionService: SDK no disponible o API key faltante")
            return
        try:
            logger.info(f"Configurando Gemini con API key: {self.api_key[:10]}...")
            genai.configure(api_key=self.api_key)
            self._initialized = True
            logger.info(f"Gemini configurado exitosamente. Modelo: {self.model_name}")
        except Exception as e:
            # No lanzamos excepciones: el servicio fallará en silencio devolviendo []
            logger.error(f"Error al configurar Gemini: {e}")
            self._initialized = False
    
    def _get_puc_for_owner(self, owner_id: str) -> list[dict[str, Any]]:
        """
        Obtiene el PUC personalizado del owner desde el repositorio.
        Si no tiene PUC cargado, usa el fallback del puc_ingresos.json.
        
        Returns: Lista de diccionarios con id, codigo, nombre, categoria, clase
        """
        if not self.puc_repository:
            logger.warning("⚠️ No hay repositorio PUC configurado, usando fallback")
            return self._load_puc_fallback()
        
        try:
            # Obtener todas las cuentas del owner
            accounts, total = self.puc_repository.list_by_owner(
                owner_id=owner_id,
                search=None,
                limit=10000,
                offset=0,
            )
            
            if not accounts:
                logger.warning(f"⚠️ Owner {owner_id} no tiene PUC cargado, usando fallback")
                return self._load_puc_fallback()
            
            # Convertir a formato simple para el prompt - INCLUIR ID
            puc_data = [
                {
                    "id": acc.id,  # ID de Firestore para referencia posterior
                    "codigo": acc.codigo,
                    "nombre": acc.nombre,
                    "categoria": acc.categoria,
                    "clase": acc.clase,
                    "nivel_agrupacion": acc.nivel_agrupacion,
                }
                for acc in accounts
            ]
            
            logger.info(f"✅ Cargadas {len(puc_data)} cuentas PUC personalizadas para owner {owner_id}")
            return puc_data
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo PUC del repositorio: {e}")
            return self._load_puc_fallback()
    
    def _load_puc_fallback(self) -> list[dict[str, Any]]:
        """Carga el PUC fallback desde puc_ingresos.json"""
        try:
            puc_path = Path(__file__).parent.parent.parent.parent / "puc_ingresos.json"
            if puc_path.exists():
                with open(puc_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info("✅ Catálogo PUC de ingresos fallback cargado")
                
                # Convertir formato del JSON a lista plana
                accounts = []
                for grupo in data.get("grupos", []):
                    for cuenta in grupo.get("cuentas", []):
                        accounts.append({
                            "codigo": cuenta.get("codigo", ""),
                            "nombre": cuenta.get("nombre", ""),
                            "categoria": "Ingresos",
                            "clase": "Ingresos",
                            "nivel_agrupacion": "Transaccional",
                        })
                return accounts
            else:
                logger.warning(f"⚠️ No se encontró puc_ingresos.json en {puc_path}")
                return []
        except Exception as e:
            logger.error(f"❌ Error cargando PUC fallback: {e}")
            return []

    # ------------------ API PÚBLICA ------------------

    def generate_suggestions(
        self, 
        invoice_payload: dict[str, object],
        owner_id: str | None = None,
    ) -> list[dict[str, object]]:
        """
        Genera sugerencias contables por línea de factura.
        Usa el PUC personalizado del owner si está disponible.
        Retorna [] si no puede generar/parsear.
        
        Args:
            invoice_payload: Datos de la factura
            owner_id: ID del propietario para obtener su PUC personalizado
        """
        logger.info("Iniciando generación de sugerencias con Gemini")
        logger.info(f"   _initialized: {self._initialized}")
        logger.info(f"   genai disponible: {genai is not None}")
        logger.info(f"   owner_id: {owner_id}")
        
        if genai is None or not self._initialized:
            logger.warning("Gemini no inicializado o SDK no disponible")
            return []

        prompt = self._build_prompt(invoice_payload, owner_id)
        if not prompt:
            logger.warning("Prompt vacío, no se puede generar sugerencias")
            return []

        logger.info(f"Prompt generado ({len(prompt)} caracteres)")
        logger.debug(f"Prompt completo:\n{prompt[:500]}...")

        try:
            logger.info(f"Llamando a Gemini modelo: {self.model_name}")
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(
                prompt,
                generation_config=getattr(genai.types, "GenerationConfig", dict)(
                    temperature=0.2,
                    max_output_tokens=8192,  # Aumentado de 2048 a 8192
                ),
            )
            logger.info("Respuesta recibida de Gemini")
            logger.info(f"   Tipo de respuesta: {type(response)}")
            logger.info(f"   Dir de respuesta: {dir(response)}")
            
            # Log completo de la respuesta para debugging
            try:
                logger.info(f"   response.text disponible: {hasattr(response, 'text')}")
                logger.info(f"   response.candidates disponible: {hasattr(response, 'candidates')}")
                if hasattr(response, 'candidates') and response.candidates:
                    logger.info(f"   Número de candidates: {len(response.candidates)}")
                    first = response.candidates[0]
                    logger.info(f"   finish_reason: {getattr(first, 'finish_reason', 'N/A')}")
                    if hasattr(response, 'usage_metadata'):
                        logger.info(f"   usage_metadata: {response.usage_metadata}")
            except Exception as e:
                logger.error(f"   Error inspeccionando respuesta: {e}")
            
        except Exception as e:
            logger.error(f"Error al llamar a Gemini: {e}", exc_info=True)
            return []

        # Extraer texto de respuesta con tolerancia a cambios del SDK
        text = self._extract_text(response)
        if not text:
            logger.warning("No se pudo extraer texto de la respuesta")
            logger.warning(f"   Respuesta completa (repr): {repr(response)}")
            return []

        logger.info(f"Texto extraído ({len(text)} caracteres)")
        logger.debug(f"Primeros 300 caracteres: {text[:300]}")

        # Intento 1: JSON directo (con o sin ```json ... ```)
        parsed = self._try_parse_json(text)
        if isinstance(parsed, list):
            logger.info(f"JSON parseado exitosamente como lista: {len(parsed)} sugerencias")
            return [item for item in parsed if isinstance(item, dict)]
        if isinstance(parsed, dict) and "suggestions" in parsed:
            raw = parsed.get("suggestions")
            if isinstance(raw, list):
                logger.info(f"JSON parseado exitosamente (campo 'suggestions'): {len(raw)} sugerencias")
                return [item for item in raw if isinstance(item, dict)]

        # Intento 2: Fallback a texto plano "codigo | razon | confianza"
        logger.warning("No se pudo parsear JSON, intentando parseo de texto plano")
        result = list(self._parse_from_text(text))
        logger.info(f"Parseadas {len(result)} sugerencias desde texto plano")
        return result

    # ------------------ HELPERS ------------------

    def _extract_text(self, response: Any) -> str:
        """
        Extrae texto de la respuesta del SDK de forma segura,
        intentando .text y, si no está, armando desde candidates/parts.
        """
        # 1) Camino feliz: .text
        try:
            text = getattr(response, "text", None)
            if isinstance(text, str) and text.strip():
                logger.debug("Texto extraído usando response.text")
                return text.strip()
        except Exception as e:
            logger.debug(f"No se pudo usar response.text: {e}")
            pass

        # 2) Intentar candidates -> parts -> text
        try:
            logger.debug("🔍 Intentando extraer desde candidates/parts")
            candidates = getattr(response, "candidates", None)
            if not candidates:
                logger.warning("No hay candidates en la respuesta")
                return ""
            parts_text: list[str] = []
            for cand in candidates:
                content = getattr(cand, "content", None)
                if not content:
                    continue
                parts = getattr(content, "parts", None)
                if not parts:
                    continue
                for p in parts:
                    t = getattr(p, "text", None)
                    if isinstance(t, str) and t.strip():
                        parts_text.append(t.strip())
            result = "\n".join(parts_text).strip()
            logger.debug(f"Texto extraído desde candidates/parts: {len(result)} caracteres")
            return result
        except Exception as e:
            logger.error(f"Error extrayendo texto desde candidates/parts: {e}")
            return ""

    def _try_parse_json(self, raw: str) -> Any:
        """
        Intenta parsear JSON eliminando fences de markdown si existen.
        """
        s = raw.strip()
        # Remover fences ```json ... ``` o ```
        if s.startswith("```json"):
            logger.debug("🔧 Removiendo fence ```json")
            s = s[7:]
        if s.startswith("```"):
            logger.debug("🔧 Removiendo fence ```")
            s = s[3:]
        if s.endswith("```"):
            logger.debug("🔧 Removiendo fence final ```")
            s = s[:-3]
        s = s.strip()

        try:
            result = json.loads(s)
            logger.debug(f"JSON parseado exitosamente: {type(result)}")
            return result
        except Exception as e:
            logger.warning(f"No se pudo parsear como JSON: {e}")
            logger.debug(f"Contenido que falló: {s[:200]}...")
            return None

    def _build_prompt(self, invoice_payload: dict[str, object], owner_id: str | None = None) -> str:
        """
        Construye el prompt para analizar la factura y producir un array JSON de sugerencias.
        Usa el PUC personalizado del owner si está disponible.
        """
        supplier = self._safe_dict(invoice_payload.get("supplier"))
        customer = self._safe_dict(invoice_payload.get("customer"))
        lines = invoice_payload.get("lines")
        if not isinstance(lines, list) or not lines:
            logger.warning("No hay líneas en la factura")
            return ""

        logger.info(f"Construyendo prompt para {len(lines)} líneas")
        
        # Obtener PUC personalizado del owner
        puc_accounts = []
        if owner_id:
            puc_accounts = self._get_puc_for_owner(owner_id)
        else:
            logger.warning("⚠️ No se proporcionó owner_id, usando PUC fallback")
            puc_accounts = self._load_puc_fallback()

        summary: list[str] = [
            "Eres un experto contador colombiano especializado en el Plan Único de Cuentas (PUC).",
            "",
            "CONTEXTO: Factura Electrónica de Venta según DIAN 2.1 (UBL 2.1)",
            "Perfil: DIAN 2.1: Factura Electrónica de Venta",
            "",
            "TAREA: Analiza cada línea de venta y asigna el código PUC más apropiado del catálogo personalizado de la empresa.",
            "",
            f"Vendedor: {supplier.get('name', 'N/A')} - NIT: {supplier.get('tax_id', 'N/A')}",
            f"Cliente: {customer.get('name', 'N/A')} - NIT: {customer.get('tax_id', 'N/A')}",
            f"Total factura: ${self._fmt_amount(invoice_payload.get('total_amount', 0))} {invoice_payload.get('currency', 'COP')}",
            "",
            "LÍNEAS DE PRODUCTOS/SERVICIOS VENDIDOS:",
        ]

        # Limitar a 15 líneas para reducir tokens
        for idx, line in enumerate(lines[:15], start=1):
            if not isinstance(line, dict):
                continue
            description = str(line.get("description", "") or "")
            amount = line.get("amount", 0)
            quantity = line.get("quantity", 1)
            summary.append(f'{idx}. "{description}" - ${self._fmt_amount(amount)} (x{quantity})')

        # Agregar catálogo PUC personalizado
        summary.extend([
            "",
            "═══════════════════════════════════════════════════════════════",
            "CATÁLOGO PUC PERSONALIZADO DE LA EMPRESA (solo usar estos códigos)",
            "═══════════════════════════════════════════════════════════════",
            "",
        ])

        if puc_accounts:
            logger.info(f"📋 Agregando {len(puc_accounts)} cuentas PUC al prompt")
            
            # Crear un JSON compacto con todas las cuentas
            summary.append("A continuación, el CATÁLOGO COMPLETO de cuentas PUC en formato JSON:")
            summary.append("```json")
            
            # Formatear como JSON compacto
            import json
            puc_json = json.dumps(puc_accounts, ensure_ascii=False, indent=2)
            summary.append(puc_json)
            summary.append("```")
            summary.append("")
        else:
            summary.extend([
                "⚠️ No se ha cargado un PUC personalizado.",
                "Por favor, sube tu catálogo PUC usando el endpoint /puc/upload",
                "",
            ])

        summary.extend(
            [
                "═══════════════════════════════════════════════════════════════",
                "INSTRUCCIONES DE CLASIFICACIÓN:",
                "═══════════════════════════════════════════════════════════════",
                "",
                "1. Analiza CADA línea de producto/servicio de la factura",
                "2. Para CADA línea, busca en el catálogo JSON la cuenta PUC más apropiada",
                "3. Usa el campo 'id' de la cuenta seleccionada (importante para referencia)",
                "4. Usa el campo 'codigo' exacto de la cuenta seleccionada",
                "5. NO inventes códigos - SOLO usa los que están en el catálogo JSON",
                "",
                "CRITERIOS DE SELECCIÓN:",
                "- Lee cuidadosamente la descripción del producto/servicio",
                "- Analiza el tipo de transacción (venta, servicio, etc.)",
                "- Compara con los 'nombre', 'categoria' y 'clase' de las cuentas PUC",
                "- Elige la cuenta que mejor coincida semánticamente",
                "- Si hay múltiples opciones similares, elige la más específica",
                "",
                "═══════════════════════════════════════════════════════════════",
                "FORMATO DE RESPUESTA:",
                "═══════════════════════════════════════════════════════════════",
                "",
                "Responde ÚNICAMENTE con un array JSON (sin markdown, sin ```json):",
                "",
                '[',
                '  {',
                '    "line_number": 1,',
                '    "puc_account_id": "uuid-de-la-cuenta-puc",',
                '    "account_code": "41350101",',
                '    "account_name": "Venta de mercancías al por mayor",',
                '    "rationale": "Este producto/servicio corresponde a [tipo de operación]. Se clasifica como [categoría] porque [razón específica]. La cuenta seleccionada es apropiada dado que [justificación basada en el nombre/categoría de la cuenta del catálogo PUC].",',
                '    "confidence": 0.95',
                '  },',
                '  {',
                '    "line_number": 2,',
                '    "puc_account_id": "uuid-de-otra-cuenta",',
                '    "account_code": "41400501",',
                '    "account_name": "Ingresos operacionales - Restaurante",',
                '    "rationale": "Se trata de un servicio de alimentación. Se clasifica en la categoría de servicios de restaurante porque involucra la preparación y venta de alimentos. Esta cuenta del PUC es la indicada para registrar ingresos por este tipo de actividad comercial.",',
                '    "confidence": 0.90',
                '  }',
                ']',
                "",
                "CAMPOS OBLIGATORIOS:",
                "- line_number: número de línea (1, 2, 3...)",
                "- puc_account_id: campo 'id' de la cuenta PUC seleccionada del catálogo JSON",
                "- account_code: campo 'codigo' de la cuenta PUC seleccionada",
                "- account_name: campo 'nombre' de la cuenta PUC seleccionada",
                "- rationale: explicación DETALLADA (150-250 caracteres) que incluya:",
                "    * Qué tipo de operación/producto/servicio es",
                "    * Por qué se clasifica en esa categoría",
                "    * Cómo coincide con la cuenta PUC seleccionada",
                "    * Cualquier detalle relevante del vendedor/cliente si aplica",
                "- confidence: número entre 0 y 1",
                "",
                "IMPORTANTE:",
                "- Los valores puc_account_id, account_code y account_name DEBEN venir del catálogo JSON",
                "- NO inventes IDs ni códigos",
                "- El rationale debe ser informativo y profesional (piensa como un contador explicando)",
                "- Menciona elementos específicos de la descripción del producto/servicio",
                "- Explica claramente la conexión entre la transacción y la cuenta PUC",
                "- Si el vendedor/cliente tiene actividad relevante, menciónalo",
                "- Si no encuentras una cuenta apropiada, explica por qué y usa confidence bajo (< 0.5)",
                "",
                "EJEMPLO DE BUEN RATIONALE:",
                '"El vendedor es una droguería que comercializa productos farmacéuticos. Este ítem corresponde a ',
                'la venta de mercancías del giro comercial principal (productos de salud). Se clasifica en la cuenta ',
                'de \'Comercio al por mayor y al detal\' ya que refleja los ingresos operacionales por la actividad ',
                'comercial de compra-venta de productos. Esta es la clasificación apropiada según el PUC para empresas ',
                'del sector comercio."',
            ]
        )

        return "\n".join(summary)

    def _parse_from_text(self, content: str) -> Iterable[dict[str, object]]:
        """
        Fallback: líneas con formato "codigo | razon | confianza"
        """
        for line in content.splitlines():
            if "|" not in line:
                continue
            cleaned = line.strip().lstrip("- ")
            parts = [segment.strip() for segment in cleaned.split("|")]
            if not parts or not parts[0]:
                continue

            suggestion: dict[str, object] = {"account_code": parts[0]}
            if len(parts) >= 2 and parts[1]:
                suggestion["rationale"] = parts[1]
            if len(parts) >= 3:
                try:
                    suggestion["confidence"] = float(parts[2])
                except ValueError:
                    pass
            yield suggestion

    # ------------------ UTILIDADES ------------------

    @staticmethod
    def _safe_dict(value: object) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _fmt_amount(value: object) -> str:
        try:
            n = float(value)  # admite int/str/Decimal convertibles
        except Exception:
            n = 0.0
        # Formato 1,234,567.89 (internacional)
        return f"{n:,.2f}"