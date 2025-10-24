# Frontend React + Vite

SPA en React y TypeScript que consume el backend de FastAPI para completar el flujo autenticación → carga de XML → sugerencias IA → exportación de reportes. Todo el contenido se valida con las facturas reales almacenadas en `../backend/app/assessment-files/`.

## Requisitos
- Node.js 18+
- npm 9+

## Configuración local
1. Instalar dependencias: `npm install`.
2. Crear `.env.local` con `VITE_API_BASE=http://localhost:8000`.
3. Ejecutar `npm run dev` para iniciar el servidor de desarrollo.
4. Ejecutar `npm run build` y `npm run preview` para validar la compilación de producción.

## Política de docstrings
La política general del repositorio aplica también aquí: solo se documentan con comentarios las funciones auxiliares críticas y siempre en español cuando sea estrictamente necesario.

## Despliegue en Vercel
1. Conectar el directorio `frontend/` a un proyecto en Vercel.
2. Definir `VITE_API_BASE` apuntando al dominio público del backend (por ejemplo, el desplegado en Railway).
3. Activar la opción de construcción automática (`npm run build`).
4. Verificar que el dashboard interactúe con las facturas y sugerencias proporcionadas por el backend.

## Dependencias clave
- React Router para navegación.
- React Query para manejo de estado remoto.
- Tailwind CSS para estilos.
- Componentes reutilizables (`InvoiceTable`, `UploadInvoiceModal`, `SuggestionPanel`, etc.) alineados con los endpoints del backend.
