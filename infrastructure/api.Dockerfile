# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm
WORKDIR /app
COPY pyproject.toml requirements.lock ./
COPY apps/api ./apps/api
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then PIP_CERT=/run/secrets/proxy_ca pip install --no-cache-dir -r requirements.lock; else pip install --no-cache-dir -r requirements.lock; fi
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then PIP_CERT=/run/secrets/proxy_ca pip install --no-deps .; else pip install --no-deps .; fi
RUN useradd -m -u 10001 company
COPY alembic.ini ./
COPY config ./config
RUN chmod -R a+rX /app
USER company
EXPOSE 8000
CMD ["uvicorn", "company_os.api:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
