# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS web
WORKDIR /app
COPY package.json package-lock.json ./
COPY apps/web/package.json ./apps/web/package.json
COPY packages/codex-worker/package.json ./packages/codex-worker/package.json
RUN npm ci --workspace=@company/web --include-workspace-root
COPY apps/web ./apps/web
ENV API_URL=http://127.0.0.1:8000
RUN npm run build -w @company/web

FROM python:3.12-slim-bookworm
WORKDIR /app
COPY --from=web /usr/local/bin/node /usr/local/bin/node
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock
COPY apps/api ./apps/api
RUN pip install --no-deps .
COPY alembic.ini ./
COPY config ./config
COPY infrastructure/staging_entrypoint.py ./infrastructure/staging_entrypoint.py
COPY --from=web /app/apps/web/.next/standalone ./
COPY --from=web /app/apps/web/.next/static ./apps/web/.next/static
RUN useradd -m -u 10001 company && chmod -R a+rX /app
USER company
ENV NODE_ENV=production HOSTNAME=0.0.0.0 RUNTIME=staging SECURE_COOKIES=true
EXPOSE 10000
CMD ["python", "infrastructure/staging_entrypoint.py"]
