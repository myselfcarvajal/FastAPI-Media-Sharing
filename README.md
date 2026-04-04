# FastAPI Photo & Video Sharing

API en FastAPI para subir y compartir fotos/vídeos (ImageKit + PostgreSQL) y frontend en Streamlit.

## Requisitos

- [uv](https://docs.astral.sh/uv/) instalado
- PostgreSQL accesible (la URL va en `.env`)
- Credenciales de ImageKit (opcional para probar solo la API sin subidas reales según tu configuración)

## Configuración

1. Clona el repositorio y entra al directorio del proyecto.

2. Copia las variables de entorno y rellénalas:

   ```bash
   cp .env.template .env
   ```

   Ajusta al menos `DATABASE_URL` y, si vas a subir medios, `IMAGEKIT_*`.

3. Instala dependencias con uv (crea el entorno virtual y sincroniza el lockfile):

   ```bash
   uv sync
   ```

## Ejecutar el proyecto

Hace falta **dos terminales**: una para el backend y otra para el frontend de Streamlit.

### Backend (FastAPI + Uvicorn)

```bash
uv run main.py
```

- API: [http://localhost:8000](http://localhost:8000)
- Documentación interactiva: [http://localhost:8000/docs](http://localhost:8000/docs)

### Frontend (Streamlit)

```bash
uv run streamlit run frontend.py
```

- Interfaz: [http://localhost:8501](http://localhost:8501)

El frontend llama al backend en `http://localhost:8000`; mantén ambos procesos en marcha mientras uses la app.
