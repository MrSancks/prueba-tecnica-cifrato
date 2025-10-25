"""
Dominio de PUC (Plan Único de Cuentas) personalizado por empresa.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import uuid


@dataclass(slots=True)
class PUCAccount:
    """
    Representa una cuenta del Plan Único de Cuentas (PUC) personalizado de una empresa.
    """
    id: str
    owner_id: str  # ID del usuario/empresa dueño de este PUC
    codigo: str  # Código de la cuenta (ej: "11050501")
    nombre: str  # Nombre de la cuenta (ej: "Efectivo CL 72")
    categoria: str  # Categoría (ej: "Caja - Bancos")
    clase: str  # Clase (ej: "Activo")
    relacion_con: str  # Relación con (ej: "Formas de pago")
    maneja_vencimientos: str  # "Maneja vencimiento" o "No maneja vencimiento"
    diferencia_fiscal: str  # "Sí" o "No"
    activo: str  # "Sí" o "No"
    nivel_agrupacion: str  # "Transaccional", "Agrupación", etc.
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        owner_id: str,
        codigo: str,
        nombre: str,
        categoria: str = "",
        clase: str = "",
        relacion_con: str = "",
        maneja_vencimientos: str = "",
        diferencia_fiscal: str = "",
        activo: str = "",
        nivel_agrupacion: str = "",
    ) -> "PUCAccount":
        """Crea una nueva cuenta PUC"""
        return cls(
            id=str(uuid.uuid4()),
            owner_id=owner_id,
            codigo=codigo.strip(),
            nombre=nombre.strip(),
            categoria=categoria.strip(),
            clase=clase.strip(),
            relacion_con=relacion_con.strip(),
            maneja_vencimientos=maneja_vencimientos.strip(),
            diferencia_fiscal=diferencia_fiscal.strip(),
            activo=activo.strip(),
            nivel_agrupacion=nivel_agrupacion.strip(),
            created_at=datetime.utcnow(),
        )
