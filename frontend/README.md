# Frontend React + Vite

SPA en React y TypeScript que consume el backend de FastAPI para completar el flujo autenticación → carga de XML → sugerencias IA → exportación de reportes. Todo el contenido se valida con las facturas reales almacenadas en `../backend/app/assessment-files/`.

## Instrucciones para ejecutar el proyecto localmente

### Requisitos
- Node.js 18+
- npm 9+

### Pasos de configuración

1. **Instalar dependencias**
   ```bash
   npm install
   ```

2. **Configurar variables de entorno**
   
   Crear un archivo `.env.local` en la raíz del directorio `frontend/` con el siguiente contenido:
   ```
   VITE_API_BASE=http://localhost:8000
   ```

3. **Ejecutar el servidor de desarrollo**
   ```bash
   npm run dev
   ```
   
   La aplicación estará disponible en `http://localhost:5173`

4. **Compilar para producción (opcional)**
   ```bash
   npm run build
   npm run preview
   ```

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
