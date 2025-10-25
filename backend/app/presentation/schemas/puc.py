"""
Schemas para las APIs de PUC (Plan Único de Cuentas).
"""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field

from app.domain.puc import PUCAccount


class PUCAccountResponse(BaseModel):
    """Schema de respuesta para una cuenta PUC"""
    
    id: str
    codigo: str
    nombre: str
    categoria: str = ""
    clase: str = ""
    relacion_con: str = ""
    maneja_vencimientos: str = ""
    diferencia_fiscal: str = ""
    activo: str = ""
    nivel_agrupacion: str = ""
    created_at: datetime
    
    @classmethod
    def from_domain(cls, account: PUCAccount) -> "PUCAccountResponse":
        """Convierte entidad de dominio a schema de respuesta"""
        return cls(
            id=account.id,
            codigo=account.codigo,
            nombre=account.nombre,
            categoria=account.categoria,
            clase=account.clase,
            relacion_con=account.relacion_con,
            maneja_vencimientos=account.maneja_vencimientos,
            diferencia_fiscal=account.diferencia_fiscal,
            activo=account.activo,
            nivel_agrupacion=account.nivel_agrupacion,
            created_at=account.created_at,
        )


class PUCListResponse(BaseModel):
    """Schema de respuesta para lista paginada de cuentas PUC"""
    
    cuentas: list[PUCAccountResponse]
    total: int = Field(description="Total de cuentas que coinciden con la búsqueda")
    page: int = Field(description="Página actual")
    page_size: int = Field(description="Tamaño de página")
    total_pages: int = Field(description="Total de páginas")


class PUCUploadResponse(BaseModel):
    """Schema de respuesta al subir un archivo PUC"""
    
    total_cuentas: int = Field(description="Número total de cuentas cargadas")
    mensaje: str = Field(description="Mensaje de confirmación")


class PUCStatsResponse(BaseModel):
    """Schema de respuesta para estadísticas de PUC"""
    
    total_cuentas: int = Field(description="Total de cuentas PUC del usuario")
    tiene_puc: bool = Field(description="Indica si el usuario tiene PUC cargado")
