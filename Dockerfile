FROM python:3.13-slim

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend backend

EXPOSE 8002

# Shell form (not exec/JSON form) so $PORT actually expands - hosts like
# Render assign their own port via this env var at runtime, defaulting to
# 8002 for plain `docker run` / local use.
CMD uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8002}
