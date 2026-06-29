# databricks-transform-mcp

A Databricks App that hosts the [Coalesce Transform MCP server](https://github.com/Coalesce-Software-Inc/coalesce-transform-mcp) over HTTP so Databricks Genie (and other HTTP MCP clients) can connect to it.

## How it works

```
Genie / AI Agent
      │
      │  HTTPS  (Databricks App proxy handles auth)
      ▼
Databricks App  (this repo)
      │
      │  supergateway bridges HTTP ↔ stdio
      ▼
coalesce-transform-mcp  (npm package, 100+ tools)
      │
      ▼
Coalesce API  +  Snowflake
```

`supergateway` wraps the stdio-only MCP binary and exposes two HTTP transports:

| Transport | Path | Use for |
|-----------|------|---------|
| Streamable HTTP | `/mcp` | Genie, newer MCP clients |
| SSE | `/sse` + `/message` | Legacy MCP clients |
| Health | `/health` | Databricks App health checks |

---

## Prerequisites

- Databricks workspace with Apps enabled
- Coalesce access token (from Coalesce Deploy → Settings → API Tokens)
- Node.js ≥ 22 on the App cluster (DBR 16+ or Apps runtime with Node 22)
- Databricks CLI installed locally

---

## 1. Create Databricks Secrets

```bash
# Create a secret scope
databricks secrets create-scope coalesce-mcp

# Store your Coalesce API token
databricks secrets put-secret coalesce-mcp access-token
# paste your token when prompted

# Optional: Snowflake credentials for run/create operations
# databricks secrets put-secret coalesce-mcp snowflake-account
# databricks secrets put-secret coalesce-mcp snowflake-user
# databricks secrets put-secret coalesce-mcp snowflake-private-key
```

---

## 2. Configure app.yaml

Edit `app.yaml` and update `MCP_BASE_URL` to match your workspace and app name:

```yaml
- name: MCP_BASE_URL
  value: https://adb-<workspace-id>.<region>.azuredatabricks.net/apps/coalesce-transform-mcp
```

You can get the exact URL from the Databricks Apps UI after the first deploy.

If you want read-only mode (safe for exploration), uncomment:
```yaml
- name: COALESCE_MCP_READ_ONLY
  value: "true"
```

---

## 3. Deploy

Push this repo to a Databricks Git Folder (Repo), then deploy via UI or CLI:

```bash
# Via Databricks CLI (Apps must be enabled in your workspace)
databricks apps deploy coalesce-transform-mcp \
  --source-code-path /Workspace/Repos/<your-user>/databricks-transform-mcp
```

Or through the Apps UI:
1. Go to **Compute → Apps → Create App**
2. Choose **Custom** app type
3. Point to this Git Folder
4. Click **Deploy**

---

## 4. Connect Genie

After the app is running, connect Genie to the MCP server:

1. In your Databricks workspace, go to **Genie → Settings → MCP Servers**
2. Add a new server with the **Streamable HTTP** endpoint:
   ```
   https://<workspace-host>/apps/coalesce-transform-mcp/mcp
   ```
3. Authentication is handled automatically by Databricks (the App proxy enforces workspace auth)

For the AI Agent Framework (Python SDK), use:
```python
from databricks.sdk import WorkspaceClient
# or configure your agent to call the /mcp endpoint with a Databricks PAT
```

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `COALESCE_ACCESS_TOKEN` | Yes | Bearer token from Coalesce Deploy |
| `COALESCE_BASE_URL` | No | Region base URL (default: US `https://app.coalescesoftware.io`) |
| `MCP_BASE_URL` | Yes | External URL of this Databricks App (used by SSE clients) |
| `COALESCE_REPO_PATH` | No | Path to local Coalesce repo for repo-backed tools |
| `COALESCE_MCP_READ_ONLY` | No | Set `"true"` to disable write/delete tools |
| `SNOWFLAKE_ACCOUNT` | No | Snowflake account identifier |
| `SNOWFLAKE_USER` | No | Snowflake username |
| `SNOWFLAKE_PRIVATE_KEY` | No | Snowflake private key (PEM) for key-pair auth |
| `DATABRICKS_APP_PORT` | Auto | Injected by Databricks Apps runtime |

---

## Local Testing

```bash
npm install

# Set env vars
export COALESCE_ACCESS_TOKEN=your-token
export COALESCE_BASE_URL=https://app.coalescesoftware.io
export DATABRICKS_APP_PORT=8000
export MCP_BASE_URL=http://localhost:8000

bash start.sh
```

Then test the health endpoint:
```bash
curl http://localhost:8000/health
```

And the MCP endpoint (streamable HTTP):
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```
