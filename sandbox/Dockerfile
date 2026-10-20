# syntax=docker/dockerfile:1
# Build and audit this as a Daytona snapshot; do not execute untrusted code on the host.
FROM node:22-bookworm-slim AS worker
WORKDIR /opt/company
COPY package.json package-lock.json ./
COPY apps/web/package.json ./apps/web/package.json
COPY packages/codex-worker ./packages/codex-worker
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then NODE_EXTRA_CA_CERTS=/run/secrets/proxy_ca npm ci --workspace=@company/codex-worker --include-workspace-root --strict-ssl=true; else npm ci --workspace=@company/codex-worker --include-workspace-root --strict-ssl=true; fi
RUN npm run build -w @company/codex-worker
FROM python:3.12-slim-bookworm
COPY --from=worker /usr/local/bin/node /usr/local/bin/node
COPY --from=worker /opt/company/node_modules /opt/company/node_modules
COPY --from=worker /opt/company/packages/codex-worker /opt/company/codex-worker
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then PIP_CERT=/run/secrets/proxy_ca pip install fastapi uvicorn httpx pytest; else pip install fastapi uvicorn httpx pytest; fi
COPY sandbox/export.py sandbox/benchmark.py /opt/company/
RUN useradd -m -u 10000 daytona && mkdir -p /workspace/repo && chown -R daytona:daytona /workspace && chmod -R a+rX,go-w /opt/company
USER daytona
WORKDIR /workspace/repo
