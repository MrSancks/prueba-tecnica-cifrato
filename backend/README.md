# Cifrato Backend - API de Facturas Electrónicas (FastAPI)

Sistema de procesamiento de facturas electrónicas colombianas (DIAN) con sugerencias PUC inteligentes usando IA generativa.  
El backend implementa **Clean Architecture** sobre **FastAPI** y utiliza las facturas XML/PDF en `app/assessment-files/` para validar parseo, reglas de IA y exportación.

---

## Instrucciones para ejecutar el proyecto localmente

### Requisitos previos

- **Python 3.13+**
- **pip**
- **API Key de Gemini (Google AI Studio)** - obligatoria para las sugerencias con IA
- **Firebase Admin** - opcional (para producción)

### 1. Clonar el repositorio
```bash
git clone https://github.com/MrSancks/prueba-tecnica-cifrato.git
cd backend
```

### 2. Crear y activar entorno virtual

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crear archivo `.env` en la raíz del proyecto:

```env
# Seguridad
SECRET_KEY=tu-clave-secreta-super-segura-cambiar-en-produccion
TOKEN_EXPIRE_MINUTES=30

# IA - Gemini (obligatorio)
GEMINI_API_KEY=tu-api-key-de-google-cloud

# Firebase (opcional - para producción)
FIREBASE_PROJECT_ID=cifrato-sandbox
FIREBASE_CREDENTIALS_JSON=""
```

**Cómo obtener la API Key de Gemini:**
1. Visitar https://aistudio.google.com/app/apikey
2. Crear o seleccionar un proyecto
3. Generar la API Key
4. Pegar la clave en `GEMINI_API_KEY`

### 5. Iniciar el servidor
```bash
uvicorn app.main:app --reload --log-level info
```

El servidor estará disponible en: **http://localhost:8000**

### 6. Documentación interactiva
- Swagger UI: http://localhost:8000/docs  
- ReDoc: http://localhost:8000/redoc

---

## Ejecutar tests

```bash
# Todos los tests
pytest

# Tests específicos
pytest tests/test_invoice_upload.py

# Cobertura
pytest --cov=app --cov-report=html

# Parser XML
pytest tests/test_parser_formats.py
pytest tests/test_all_xml.py
```

---

## Estructura del proyecto

```
backend/
├── app/
│   ├── main.py                    # Aplicación FastAPI principal
│   ├── application/               # Casos de uso (lógica de negocio)
│   │   ├── use_cases/
│   │   │   ├── auth.py            # Registro, login, autenticación
│   │   │   └── invoices.py        # Upload, listado, sugerencias, export
│   │   └── contracts/             # Interfaces (repositorios, servicios)
│   ├── domain/                    # Entidades del dominio
│   │   ├── users.py
│   │   ├── invoices.py
│   │   └── ai.py
│   ├── infrastructure/            # Implementaciones concretas
│   │   ├── repositories/          # Persistencia (Firestore, In-Memory)
│   │   └── services/
│   │       ├── ai.py              # Gemini AI - Sugerencias PUC
│   │       ├── invoice_parser.py  # Parser UBL XML (DIAN)
│   │       ├── excel_exporter.py  # Generador Excel
│   │       ├── puc_catalog.py     # Catálogo PUC Colombia
│   │       └── puc_mapper.py      # Mapeo códigos genéricos → empresa
│   ├── presentation/              # Capa de presentación (API)
│   │   ├── api.py                 # Router principal
│   │   ├── routers/               # Endpoints por módulo
│   │   ├── schemas/               # Modelos Pydantic (request/response)
│   │   └── middleware.py          # CORS, seguridad
│   └── config/                    # Configuración y dependencias
├── tests/                         # Suite de tests
├── puc_ingresos.json              # Catálogo PUC ingresos (clase 4)
├── requirements.txt               # Dependencias
├── Dockerfile                     # Contenedor Docker
└── README.md                      # Este archivo
```

---

## Arquitectura

### Clean Architecture (capas)
```
Presentation (API) → Application (Use Cases) → Domain (Entities) → Infrastructure
```
- **Domain:** Entidades de negocio puras (sin dependencias externas).
- **Application:** Casos de uso (orquesta dominio + infraestructura).
- **Infrastructure:** Implementaciones concretas (DB, APIs externas, filesystem).
- **Presentation:** Controladores FastAPI, schemas, middleware.

### Principios SOLID
- **Dependency Injection:** con `fastapi.Depends`.
- **Interface Segregation:** contratos en `application/contracts/`.
- **Single Responsibility:** cada servicio cumple un propósito único.

---

## Endpoints principales

### Autenticación
| Método | Endpoint        | Descripción                   |
|--------|------------------|-------------------------------|
| POST   | `/auth/register` | Registrar nuevo usuario       |
| POST   | `/auth/login`    | Iniciar sesión (retorna JWT)  |
| GET    | `/auth/me`       | Información del usuario actual|

### Facturas
| Método | Endpoint                      | Descripción                         |
|--------|--------------------------------|-------------------------------------|
| GET    | `/invoices`                   | Listar facturas del usuario         |
| GET    | `/invoices/{id}`              | Detalle de una factura              |
| POST   | `/invoices/upload`            | Subir factura XML                   |
| GET    | `/invoices/{id}/suggest`      | Sugerencias PUC con IA              |
| POST   | `/invoices/{id}/select`       | Seleccionar sugerencia PUC          |
| GET    | `/invoices/export`            | Exportar a Excel (dos hojas)        |

### Salud
| Método | Endpoint   | Descripción         |
|--------|------------|---------------------|
| GET    | `/health`  | Estado del servidor |

---

## Flujo de sugerencias PUC con IA

1. El usuario sube una **factura XML** (UBL DIAN).
2. El **parser** extrae datos: proveedor, productos, totales.
3. **Gemini** analiza y sugiere códigos PUC apropiados.
4. El usuario **selecciona** la mejor sugerencia.
5. El sistema **exporta** a Excel con PUC asignado.

### Catálogo PUC soportado
- **puc_ingresos.json**: 32 códigos PUC clase 4 (ingresos)
  - Grupo **41**: Operacionales (ventas, servicios)
  - Grupo **42**: No operacionales (intereses, dividendos)

### Validaciones
- Solo códigos PUC **clase 4** (ingresos) para facturas de **venta**.
- Contexto: *“Factura Electrónica de Venta DIAN 2.1”*.
- Análisis de productos y actividad económica del proveedor.

---

## Formatos XML soportados

| Formato                | Tipo      | Root Element          | Soporte |
|------------------------|-----------|------------------------|---------|
| Factura de Venta       | Directa   | `<Invoice>`           | ✅      |
| Nota Crédito           | Directa   | `<CreditNote>`        | ✅      |
| Nota Débito            | Directa   | `<DebitNote>`         | ✅      |
| Documento Adjunto      | Embebido  | `<AttachedDocument>`  | ✅      |

**AttachedDocument** con factura embebida en CDATA:
```xml
<AttachedDocument>
  <cac:Attachment>
    <cbc:Description>
      <![CDATA[ <Invoice>...</Invoice> ]]>
    </cbc:Description>
  </cac:Attachment>
</AttachedDocument>
```
El parser extrae automáticamente la factura embebida.

---

## Exportación a Excel

**Hoja 1 — Resumen**
- Datos de factura + sugerencia PUC seleccionada.
- Columnas: `ID, Fecha, Proveedor, Cliente, Total, Código PUC, Nombre PUC, Descripción, Justificación`.

**Hoja 2 — Productos**
- Detalle de líneas de productos.
- Columnas: `ID Factura, ID Producto, Descripción, Cantidad, Precio Unitario, Subtotal, Total Línea`.

---

## Docker

### Construir imagen
```bash
docker build -t cifrato-backend .
```

### Ejecutar contenedor
```bash
docker run -p 8000:8000 --env-file .env cifrato-backend
```

---

## Despliegue (Railway / Render / Fly.io)

1. Crear un **servicio web** nuevo y apuntar a este directorio (usa el `Dockerfile`).
2. Definir variables: `SECRET_KEY`, `TOKEN_EXPIRE_MINUTES`, `GEMINI_API_KEY`, `FIREBASE_PROJECT_ID`, `FIREBASE_CREDENTIALS_JSON` (si aplica).
3. Comando de inicio:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. Mantener `app/assessment-files/` en el repositorio para validar flujos en producción.
5. Desplegar.

### Variables de entorno (producción)
```env
SECRET_KEY=<openssl rand -hex 32>
TOKEN_EXPIRE_MINUTES=30
GEMINI_API_KEY=<tu-api-key-de-google-cloud>
FIREBASE_PROJECT_ID=<tu-proyecto-firebase>
FIREBASE_CREDENTIALS_JSON=<json-completo-de-service-account>  # o vacío si no aplica
```

---

## Firebase Admin SDK (opcional)

- El helper `app/infrastructure/services/firebase_admin.py` inicializa Firebase a partir de `FIREBASE_CREDENTIALS_JSON`.
- La función `firebase_project_id()` expone el `project_id` cuando hay credenciales.

---

## Política de docstrings

Los docstrings se reservan para **funciones auxiliares críticas** y se redactan en español (por ejemplo, el parser UBL).  
El resto del código se documenta con **nombres claros** y **pruebas**.

---

## Seguridad

- Autenticación mediante **JWT Bearer**.
- Mantén **`SECRET_KEY`** en secreto y cámbialo en producción.
- No expongas archivos sensibles (por ejemplo, `FIREBASE_CREDENTIALS_JSON`) fuera de variables de entorno.

---

## Contribuir

1. Haz **fork** del repositorio.
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`).
3. Commit (`git commit -m "feat: nueva funcionalidad"`).
4. Push (`git push origin feature/nueva-funcionalidad`).
5. Abre un **Pull Request**.

---

## Licencia

Proyecto privado y confidencial.

---

## Soporte

Para preguntas o problemas, contactar al equipo de desarrollo.
