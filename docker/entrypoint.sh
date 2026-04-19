#!/bin/sh
set -e

# Start ppx-align FastAPI backend
cd /app/ppx-align
uv run ppx-align serve /data &

# Start ppx-svelte Node server
cd /app/ppx-svelte
node build/index.js &

wait
