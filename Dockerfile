FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.17 /uv /usr/local/bin/uv

ENV   PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  UV_PYTHON_DOWNLOADS=never \
  UV_HTTP_TIMEOUT=100

WORKDIR /app

COPY pyproject.toml uv.lock .python-version ./

RUN uv sync --locked --no-dev --no-install-project --no-cache

COPY main.py ./
COPY pr2changelog ./pr2changelog

ENTRYPOINT ["/app/.venv/bin/python", "/app/main.py"]
