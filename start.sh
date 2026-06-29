#!/bin/bash
set -e

PORT="${DATABRICKS_APP_PORT:-8000}"
BASE_URL="${MCP_BASE_URL:-http://localhost:$PORT}"

# Install deps on first start (node_modules is ephemeral on Databricks Apps compute)
if [ ! -d "node_modules/.bin/supergateway" ]; then
  echo "[setup] Installing dependencies..."
  npm install --production --silent
fi

echo "[start] Coalesce Transform MCP server"
echo "        Port    : $PORT"
echo "        Base URL: $BASE_URL"
echo "        Endpoints:"
echo "          SSE             -> $BASE_URL/sse"
echo "          SSE messages    -> $BASE_URL/message"
echo "          Streamable HTTP -> $BASE_URL/mcp  (use this for Genie)"
echo "          Health          -> $BASE_URL/health"

exec ./node_modules/.bin/supergateway \
  --stdio "./node_modules/.bin/coalesce-transform-mcp" \
  --port "$PORT" \
  --baseUrl "$BASE_URL" \
  --ssePath /sse \
  --messagePath /message \
  --streamableHttpPath /mcp \
  --cors \
  --healthEndpoint /health \
  --logLevel info
