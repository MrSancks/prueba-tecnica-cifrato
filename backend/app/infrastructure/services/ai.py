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
    - Devuelve: list[dict[str, object]] con campos sugeridos por línea
    """
    api_key: str
    model_name: str = "gemini-2.5-flash"
    _initialized: bool = False
    _puc_ingresos: dict[str, Any] | None = None

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
            
            # Cargar PUC de ingresos
            self._load_puc_ingresos()
        except Exception as e:
            # No lanzamos excepciones: el servicio fallará en silencio devolviendo []
            logger.error(f"Error al configurar Gemini: {e}")
            self._initialized = False
    
    def _load_puc_ingresos(self) -> None:
        """Carga el catálogo de códigos PUC de ingresos (clase 4)"""
        try:
            puc_path = Path(__file__).parent.parent.parent.parent / "puc_ingresos.json"
            if puc_path.exists():
                with open(puc_path, 'r', encoding='utf-8') as f:
                    self._puc_ingresos = json.load(f)
                logger.info("✅ Catálogo PUC de ingresos cargado")
            else:
                logger.warning(f"⚠️ No se encontró puc_ingresos.json en {puc_path}")
        except Exception as e:
            logger.error(f"❌ Error cargando PUC de ingresos: {e}")

    # ------------------ API PÚBLICA ------------------

    def generate_suggestions(self, invoice_payload: dict[str, object]) -> list[dict[str, object]]:
        """
        Genera sugerencias contables por línea de factura.
        Retorna [] si no puede generar/parsear.
        """
        logger.info("Iniciando generación de sugerencias con Gemini")
        logger.info(f"   _initialized: {self._initialized}")
        logger.info(f"   genai disponible: {genai is not None}")
        
        if genai is None or not self._initialized:
            logger.warning("Gemini no inicializado o SDK no disponible")
            return []

        prompt = self._build_prompt(invoice_payload)
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

    def _build_prompt(self, invoice_payload: dict[str, object]) -> str:
        """
        Construye el prompt para analizar la factura y producir un array JSON de sugerencias.
        """
        supplier = self._safe_dict(invoice_payload.get("supplier"))
        customer = self._safe_dict(invoice_payload.get("customer"))
        lines = invoice_payload.get("lines")
        if not isinstance(lines, list) or not lines:
            logger.warning("No hay líneas en la factura")
            return ""

        logger.info(f"Construyendo prompt para {len(lines)} líneas")

        summary: list[str] = [
            "Eres un experto contador colombiano especializado en el Plan Único de Cuentas (PUC).",
            "",
            "CONTEXTO: Factura Electrónica de Venta según DIAN 2.1 (UBL 2.1)",
            "Perfil: DIAN 2.1: Factura Electrónica de Venta",
            "",
            "TAREA: Analiza cada línea de venta y asigna el código PUC de INGRESOS (clase 4) de 4 DÍGITOS más apropiado.",
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

        # Agregar catálogo PUC desde el JSON
        summary.extend([
            "",
            "═══════════════════════════════════════════════════════════════",
            "CATÁLOGO PUC COLOMBIANO - CLASE 4: INGRESOS (solo usar estos códigos)",
            "═══════════════════════════════════════════════════════════════",
            "",
        ])

        if self._puc_ingresos and isinstance(self._puc_ingresos, dict):
            for grupo in self._puc_ingresos.get("grupos", []):
                grupo_codigo = grupo.get("codigo", "")
                grupo_nombre = grupo.get("nombre", "")
                summary.append(f"GRUPO {grupo_codigo} - {grupo_nombre.upper()}:")
                summary.append("")
                
                for cuenta in grupo.get("cuentas", []):
                    codigo = cuenta.get("codigo", "")
                    nombre = cuenta.get("nombre", "")
                    summary.append(f"  {codigo}: {nombre}")
                
                summary.append("")
        else:
            # Fallback si no se cargó el JSON
            summary.extend([
                "GRUPO 41 - OPERACIONALES:",
                "  4105: Agricultura, ganadería, caza y silvicultura",
                "  4110: Pesca",
                "  4115: Explotación de minas y canteras",
                "  4120: Industrias manufactureras",
                "  4125: Suministro de electricidad, gas y agua",
                "  4130: Construcción",
                "  4135: Comercio al por mayor y al por menor",
                "  4140: Hoteles y restaurantes",
                "  4145: Transporte, almacenamiento y comunicaciones",
                "  4150: Actividad financiera",
                "  4155: Actividades inmobiliarias, empresariales y de alquiler",
                "  4160: Enseñanza",
                "  4165: Servicios sociales y de salud",
                "  4170: Otras actividades de servicios comunitarios, sociales y personales",
                "  4175: Devoluciones en ventas (DB)",
                "",
                "GRUPO 42 - NO OPERACIONALES:",
                "  4205: Otras ventas",
                "  4210: Financieros",
                "  4215: Dividendos y participaciones",
                "  4218: Ingresos método de participación",
                "  4220: Arrendamientos",
                "  4225: Comisiones",
                "  4230: Honorarios",
                "  4235: Servicios",
                "  4240: Utilidad en venta de inversiones",
                "  4245: Utilidad en venta de propiedades, planta y equipo",
                "  4248: Utilidad en venta de otros bienes",
                "  4250: Recuperaciones",
                "  4255: Indemnizaciones",
                "  4260: Participaciones en concesiones",
                "  4265: Ingresos de ejercicios anteriores",
                "  4275: Devoluciones en otras ventas (DB)",
                "  4295: Diversos",
                "",
            ])

        summary.extend(
            [
                "═══════════════════════════════════════════════════════════════",
                "INSTRUCCIONES DE CLASIFICACIÓN:",
                "═══════════════════════════════════════════════════════════════",
                "",
                "1. SOLO usa códigos de 4 DÍGITOS del catálogo anterior",
                "2. NO inventes códigos - selecciona ÚNICAMENTE de la lista",
                "3. Analiza la descripción del producto/servicio para determinar:",
                "   - ¿Es ingreso operacional (actividad principal)? → Grupo 41",
                "   - ¿Es ingreso no operacional (secundario)? → Grupo 42",
                "4. Dentro del grupo, elige el código MÁS ESPECÍFICO que coincida",
                "5. Si hay duda, usa el código más genérico del grupo apropiado",
                "",
                "CRITERIOS DE SELECCIÓN:",
                "- 4135: Para venta de productos/mercancías",
                "- 4140: Para servicios de alimentos/bebidas/alojamiento",
                "- 4155: Para servicios profesionales/consultoría/alquileres",
                "- 4145: Para servicios de transporte/logística",
                "- 4160: Para servicios educativos/capacitación",
                "- 4165: Para servicios de salud",
                "- 4235: Para otros servicios generales",
                "- 4295: Para ingresos diversos no clasificados",
                "",
                "═══════════════════════════════════════════════════════════════",
                "FORMATO DE RESPUESTA:",
                "═══════════════════════════════════════════════════════════════",
                "",
                "Responde ÚNICAMENTE con un array JSON (sin markdown, sin ```json):",
                "",
                '[',
                '  {"line_number": 1, "account_code": "4135", "rationale": "Venta de mercancía - comercio", "confidence": 0.95},',
                '  {"line_number": 2, "account_code": "4140", "rationale": "Servicio de restaurante", "confidence": 0.90}',
                ']',
                "",
                "IMPORTANTE:",
                "- account_code debe ser EXACTAMENTE 4 dígitos",
                "- account_code debe existir en el catálogo anterior",
                "- rationale debe explicar brevemente por qué se eligió ese código",
                "- confidence debe ser entre 0 y 1",
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