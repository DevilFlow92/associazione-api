FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app

# git è necessario per installare dipendenze da GitHub (associazione-api-toolkit)
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Installa dipendenze prima del codice (layer cachabile)
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen --extra r2

# Chromium per il rendering PDF via Playwright (app/services/render/pdf_renderer.py).
# --with-deps installa anche le librerie di sistema Debian richieste dal browser.
RUN uv run playwright install --with-deps chromium

# Copia il resto del codice
COPY . .

EXPOSE 8000
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
