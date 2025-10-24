# Backend FastAPI

El backend implementa Clean Architecture sobre FastAPI y utiliza las facturas XML/PDF entregadas en `app/assessment-files/` para validar parseo, reglas de IA y exportación.

## Requisitos
- Python 3.11
- `pip install -r requirements.txt`
- Variables de entorno definidas en `.env` (puedes copiar desde `../.env.example`).

## Configuración local
1. Crear un entorno virtual y activarlo.
2. Instalar dependencias: `pip install -r requirements.txt`.
3. Crear un archivo `.env` en `backend/` con:
   ```env
   SECRET_KEY=changeme
   TOKEN_EXPIRE_MINUTES=30
   AI_BASE_URL=http://localhost:11434
   AI_MODEL=phi3
   FIREBASE_PROJECT_ID=cifrato-sandbox
   FIREBASE_CREDENTIALS_JSON=""  # opcional
   ```
4. Iniciar el servidor: `uvicorn app.main:app --reload`.
5. Ejecutar pruebas: `pytest`.

## Firebase Admin SDK
- El helper `app/infrastructure/services/firebase_admin.py` inicializa Firebase a partir de `FIREBASE_CREDENTIALS_JSON` o `FIREBASE_CREDENTIALS_PATH`.
- `firebase_project_id()` expone el `project_id` del servicio `firebase-adminsdk-fbsvc@cifrato-6441d.iam.gserviceaccount.com` cuando las credenciales están presentes.

## Política de docstrings
Los docstrings se reservan para funciones auxiliares críticas y se redactan en español (por ejemplo, el parser UBL). El resto del código se documenta mediante nombres claros y pruebas.

## Despliegue en Railway
1. Crear un servicio web nuevo y apuntar a este directorio con el Dockerfile incluido.
2. Definir variables `SECRET_KEY`, `TOKEN_EXPIRE_MINUTES`, `AI_BASE_URL`, `AI_MODEL`, `FIREBASE_PROJECT_ID` y, si aplica, `FIREBASE_CREDENTIALS_JSON`/`FIREBASE_CREDENTIALS_PATH`.
3. Configurar el comando de inicio: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
4. Mantener `app/assessment-files/` en el repositorio para validar los flujos en producción.

## Endpoints clave
- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `GET /invoices`
- `GET /invoices/{invoice_id}`
- `POST /invoices/upload`
- `GET /invoices/{invoice_id}/suggest`
- `GET /invoices/export`
