# GHC-DR-Portal

## Backend

### Configuración
Crea `api/.env` desde el archivo raíz `.env.example` y configura las variables `DR_BASE_URL` y `DR_API_KEY`. Nunca subas este archivo al repositorio.

### Ejecución
1. Instala las dependencias:
   ```bash
   pip install -r api/requirements.txt
   ```
2. Inicia el servidor:
   ```bash
   uvicorn api.server:app --host 0.0.0.0 --port 8000
   ```
3. Prueba el endpoint de salud:
   ```bash
   curl http://127.0.0.1:8000/api/health
   ```

## Frontend
Run `npm install` in `web/` and start the development server with `npm run dev`.
