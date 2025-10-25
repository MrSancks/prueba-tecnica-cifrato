"""
Router de PUC (Plan Único de Cuentas) personalizado por empresa.
"""
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.application.use_cases.puc import (
    GetPUCForAI,
    GetPUCStats,
    ListPUC,
    PUCUploadError,
    UploadPUC,
)
from app.config.dependencies import (
    get_list_puc_use_case,
    get_puc_for_ai_use_case,
    get_puc_stats_use_case,
    get_upload_puc_use_case,
)
from app.presentation.dependencies.security import AuthenticatedUser
from app.presentation.schemas.puc import (
    PUCAccountResponse,
    PUCListResponse,
    PUCStatsResponse,
    PUCUploadResponse,
)

router = APIRouter(prefix="/puc", tags=["puc"])


@router.post("/upload", response_model=PUCUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_puc(
    current_user: AuthenticatedUser,
    file: UploadFile = File(..., description="Archivo Excel (.xlsx) con el PUC personalizado"),
    use_case: UploadPUC = Depends(get_upload_puc_use_case),
):
    """
    Sube un archivo Excel con el Plan Único de Cuentas (PUC) personalizado de la empresa.
    
    El archivo debe tener las siguientes columnas:
    - Código (obligatorio)
    - Nombre (obligatorio)
    - Categoría
    - Clase
    - Relación con
    - Maneja vencimientos
    - Diferencia fiscal
    - Activo
    - Nivel agrupación
    
    **Nota:** Este endpoint reemplazará cualquier PUC previamente cargado.
    """
    # Validar tipo de archivo
    if file.content_type not in {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten archivos Excel (.xlsx o .xls)",
        )
    
    # Leer contenido del archivo
    content = await file.read()
    
    try:
        result = use_case.execute(
            owner_id=current_user.id,
            file_content=content,
            filename=file.filename or "puc.xlsx",
        )
        
        return PUCUploadResponse(**result)
        
    except PUCUploadError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("", response_model=PUCListResponse)
async def list_puc(
    current_user: AuthenticatedUser,
    search: str | None = Query(None, description="Búsqueda por código, nombre, categoría o clase"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(50, ge=1, le=200, description="Tamaño de página (máx 200)"),
    use_case: ListPUC = Depends(get_list_puc_use_case),
):
    """
    Lista las cuentas PUC del usuario con paginación y búsqueda opcional.
    
    Parámetros de búsqueda:
    - **search**: Busca en código, nombre, categoría y clase
    - **page**: Número de página (inicia en 1)
    - **page_size**: Cantidad de resultados por página (1-200)
    """
    result = use_case.execute(
        owner_id=current_user.id,
        search=search,
        page=page,
        page_size=page_size,
    )
    
    return PUCListResponse(
        cuentas=[PUCAccountResponse.from_domain(acc) for acc in result["cuentas"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    )


@router.get("/stats", response_model=PUCStatsResponse)
async def get_puc_stats(
    current_user: AuthenticatedUser,
    use_case: GetPUCStats = Depends(get_puc_stats_use_case),
):
    """
    Obtiene estadísticas básicas del PUC del usuario.
    
    Útil para verificar si el usuario tiene un PUC cargado
    antes de generar sugerencias contables.
    """
    result = use_case.execute(owner_id=current_user.id)
    return PUCStatsResponse(**result)


@router.get("/export-json", response_model=list[dict])
async def export_puc_for_ai(
    current_user: AuthenticatedUser,
    use_case: GetPUCForAI = Depends(get_puc_for_ai_use_case),
):
    """
    Exporta todas las cuentas PUC en formato JSON.
    
    Este endpoint es útil para obtener el PUC completo que se
    enviará como contexto a la IA para generar sugerencias contables.
    
    **Nota:** Este endpoint puede retornar una gran cantidad de datos
    dependiendo del tamaño del PUC.
    """
    return use_case.execute(owner_id=current_user.id)
