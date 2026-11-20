# Práctica 8 - Chatbot de riesgo (FastAPI + LLM + modelo)

```
app/
  main.py               crea la API y registra los routers
  config.py             ajustes (ruta del modelo)
  routers/              endpoints: health.py, predict.py, chat.py
  schemas/              contratos Pydantic: prestamo.py, chat.py
  services/             logica: modelo.py, orquestador.py, llm.py
frontend/               app.py (Streamlit) y logo.png
models/                 modelo_impago.joblib
scripts/                entrenar_modelo.py (regenera el joblib)
tests/                  tests con pytest
pyproject.toml
```

## Arrancar

```
uv sync
uv run uvicorn app.main:app --port 8000        # backend
uv run streamlit run frontend/app.py           # frontend (otra terminal)
uv run pytest                                  # tests
```

Sin configurar nada usa un LLM simulado. Para un LLM real (LiteLLM), por ejemplo Azure OpenAI:

```
export LLM_MODEL=azure/<nombre-del-deployment>
export AZURE_API_KEY=...
export AZURE_API_BASE=https://<recurso>.openai.azure.com
export AZURE_API_VERSION=...
```

## LM Studio con Docker

1. Carga en LM Studio un modelo que soporte herramientas (tool calling).
2. Inicia su servidor en el puerto 1234 y activa **Serve on Local Network**
   para que pueda recibir conexiones desde Docker.
3. Copia `.env.example` a `.env` (`cp .env.example .env`) y sustituye
   `YOUR_MODEL_ID` por el identificador exacto del modelo
   mostrado en LM Studio, manteniendo el prefijo `openai/`.
   Si has activado autenticación, configura también `OPENAI_API_KEY` con tu token.
4. Ejecuta `docker compose up --build` y abre http://localhost:8501.

Compose pasa `.env` al contenedor de la API. Para ejecutar la API fuera de Docker,
cambia `OPENAI_API_BASE` a `http://localhost:1234/v1` y arranca con
`uv run --env-file .env uvicorn app.main:app --port 8000`.
