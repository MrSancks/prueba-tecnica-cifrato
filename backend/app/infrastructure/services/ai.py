from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, TYPE_CHECKING, Any

try:  # pragma: no cover - degradación cuando no esté httpx instalado
    import httpx
except ModuleNotFoundError:  # pragma: no cover - entorno sin dependencias binarias
    httpx = None  # type: ignore[assignment]

if TYPE_CHECKING:  # pragma: no cover - solo para tipado estático
    from httpx import Client as HTTPXClient


@dataclass(slots=True)
class OllamaAISuggestionService:
    base_url: str
    model: str
    timeout: float = 10.0
    _client: "HTTPXClient" | Any | None = None

    def __post_init__(self) -> None:
        if self._client is None and httpx is not None:
            self._client = httpx.Client(base_url=self.base_url.rstrip("/"), timeout=self.timeout)

    def generate_suggestions(self, invoice_payload: dict[str, object]) -> list[dict[str, object]]:
        if httpx is None:
            return []

        prompt = self._build_prompt(invoice_payload)
        if not prompt:
            return []

        try:
            response = self._client.post(
                "/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return []

        data = response.json()
        if isinstance(data, dict):
            raw = data.get("suggestions")
            if isinstance(raw, list):
                return [item for item in raw if isinstance(item, dict)]

            text = data.get("response")
            if isinstance(text, str):
                return list(self._parse_from_text(text))
        return []

    def _build_prompt(self, invoice_payload: dict[str, object]) -> str:
        supplier = invoice_payload.get("supplier", {})
        customer = invoice_payload.get("customer", {})
        lines = invoice_payload.get("lines", [])

        if not lines:
            return ""

        summary = [
            "Genera códigos contables colombianos para esta factura.",
            f"Proveedor: {supplier.get('name', '')} ({supplier.get('tax_id', '')}).",
            f"Cliente: {customer.get('name', '')} ({customer.get('tax_id', '')}).",
        ]

        summary.append("Detalle de productos:")
        for line in lines[:10]:
            description = getattr(line, "description", "")
            amount = getattr(line, "line_extension_amount", "")
            summary.append(f"- {description} por {amount}")

        summary.append("Responde con una lista en el formato 'codigo | razon | confianza'.")
        return "\n".join(summary)

    def _parse_from_text(self, content: str) -> Iterable[dict[str, object]]:
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

    def close(self) -> None:
        if httpx is not None and self._client is not None:
            self._client.close()
