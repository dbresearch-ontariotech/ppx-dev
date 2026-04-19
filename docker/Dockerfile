# syntax=docker/dockerfile:1

# ── Stage 1: build ppx-svelte ────────────────────────────────────────────────
FROM node:25-slim AS svelte-build

RUN npm install -g pnpm@10

WORKDIR /build/ppx-svelte
COPY ppx-svelte/pnpm-lock.yaml ppx-svelte/package.json ./
RUN pnpm install --frozen-lockfile

COPY ppx-svelte/ ./
RUN pnpm build


# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM node:25-slim AS runtime

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# --- ppx-align (Python) ---
COPY ppx-align/pyproject.toml ppx-align/uv.lock ./ppx-align/
COPY ppx-align/src ./ppx-align/src
RUN cd ppx-align && uv sync --frozen --no-dev

# --- ppx-svelte (Node) ---
COPY --from=svelte-build /build/ppx-svelte/build ./ppx-svelte/build
COPY --from=svelte-build /build/ppx-svelte/node_modules ./ppx-svelte/node_modules
COPY ppx-svelte/package.json ./ppx-svelte/

# Expose ports
EXPOSE 3000

# Both services are started by an entrypoint script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
