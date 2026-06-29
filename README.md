# databricks-transform-mcp

A Databricks App that hosts the [Coalesce Transform MCP server](https://github.com/Coalesce-Software-Inc/coalesce-transform-mcp) over HTTP so Databricks Genie can connect to it.

## How it works

```
Genie / AI Agent
      │
      │  HTTPS  (Databricks App proxy handles auth)
      ▼
Databricks App  (uvicorn + server.py)
      │
      │  Python MCP SDK bridges HTTP ↔ stdio
      ▼
coalesce-transform-mcp  (npm package, 100+ tools)
      │
      ▼
Coalesce API  +  Snowflake
```

`server.py` uses the Python MCP SDK to spin up `coalesce-transform-mcp` as a subprocess, then exposes its tools over Streamable HTTP via a Starlette/uvicorn ASGI app.

| Endpoint | Path | Use for |
|----------|------|---------|
| Streamable HTTP | `/mcp` | Genie, newer MCP clients |
| Health | `/` | Databricks App health checks |

---

## Prerequisites

- Databricks workspace with Apps enabled
- Coalesce access token (Coalesce Deploy → Settings → API Tokens)
- Node.js ≥ 22 on the App cluster (needed to run `npx coalesce-transform-mcp`)
- Python ≥ 3.11

---

## 1. Create Databricks Secrets

```bash
# Create a secret scope (skip if it already exists)
databricks secrets create-scope coalesce-mcp

# Store your Coalesce API token
databricks secrets put-secret coalesce-mcp coalesce-access-token
# paste your token when prompted
```

---

## 2. Deploy

Push this repo to a Databricks Git Folder, then deploy:

```bash
databricks apps deploy coalesce-transform-mcp \
  --source-code-path /Workspace/Repos/<your-user>/databricks-transform-mcp
```

Or via the Apps UI:
1. **Compute → Apps → Create App → Custom**
2. Point to this Git Folder
3. Click **Deploy**

On first deploy, `pip install -r requirements.txt` runs automatically, then uvicorn starts.

---

## 3. Connect Genie

1. In Genie, go to **Settings → MCP Servers → Add**
2. Set the endpoint to the Streamable HTTP path:
   ```
   https://<workspace-host>/apps/coalesce-transform-mcp/mcp
   ```
3. Auth is handled automatically by the Databricks App proxy

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `COALESCE_ACCESS_TOKEN` | Yes | Bearer token from Coalesce Deploy |
| `COALESCE_BASE_URL` | No | Region base URL (default: `https://app.coalescesoftware.io`) |
| `COALESCE_REPO_PATH` | No | Path to local Coalesce repo for repo-backed tools |
| `COALESCE_MCP_READ_ONLY` | No | Set `"true"` to disable write/delete tools |
| `SNOWFLAKE_ACCOUNT` | No | Snowflake account for run/create operations |
| `SNOWFLAKE_USER` | No | Snowflake user |
| `SNOWFLAKE_PRIVATE_KEY` | No | Snowflake private key (PEM) |

---

## Local Testing

```bash
pip install -r requirements.txt

export COALESCE_ACCESS_TOKEN=your-token
export COALESCE_BASE_URL=https://app.australia-southeast1.gcp.coalescesoftware.io

uvicorn server:app --host 0.0.0.0 --port 8000
```

Test the MCP endpoint:
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```
