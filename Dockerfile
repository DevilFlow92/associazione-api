FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app

# git è necessario per installare dipendenze da GitHub (associazione-api-toolkit)
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Installa dipendenze prima del codice (layer cachabile)
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

# Copia il resto del codice
COPY . .

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
