# PhoenixForge AI — Setup Guide (Plain English)

This walks you through getting the whole thing running in GitHub Codespaces, from zero.
No local installs needed — everything happens in the browser.

---

## Step 1: Push this project to GitHub

1. Unzip the folder you downloaded.
2. Go to github.com and create a new repository (e.g. `phoenixforge-ai`). Make it **public**
   (the hackathon requires a public repo).
3. Upload the unzipped folder's contents to that repository. The easiest way: on the new
   repo's page, click "uploading an existing file" and drag in everything, OR use GitHub
   Desktop, OR run these commands in any terminal that has git:
   ```bash
   cd phoenixforge-ai
   git init
   git add .
   git commit -m "Initial commit: PhoenixForge AI"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/phoenixforge-ai.git
   git push -u origin main
   ```
4. Double check the Apache 2.0 `LICENSE` file is at the top level of the repo (it already
   is in this zip) — GitHub will auto-detect it and show "Apache-2.0" in the About section.

## Step 2: Open it in a Codespace

1. On your repository's GitHub page, click the green **Code** button.
2. Click the **Codespaces** tab.
3. Click **Create codespace on main**.
4. Wait 1-2 minutes. A `.devcontainer` config is already included in this project, so the
   Codespace will automatically install Python and Node.js dependencies for you — you
   don't need to run any install commands yourself.

## Step 3: Add your Anthropic API key

The agents use Claude to do their reasoning and code generation, so you need one API key.

1. In the Codespace's file explorer (left side), open `backend/.env.example`.
2. Make a copy of it named `.env` in the same folder (`backend/.env`). You can do this by
   right-clicking `backend/.env.example` → Copy, then right-click the `backend` folder →
   Paste, then rename the copy to `.env`. Or just run this in the terminal:
   ```bash
   cp backend/.env.example backend/.env
   ```
3. Open `backend/.env` and replace `your_anthropic_api_key_here` with your real Anthropic
   API key.
4. Leave `DEMO_MODE=true` — this is what lets the whole thing run without needing a real
   DataHub instance or GitHub token. (GitHub and DataHub tokens are optional — see Step 6.)

## Step 4: Start the backend

In the Codespace's terminal, run:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You'll see a popup in the bottom-right of the screen saying a port was forwarded. Leave
this terminal running — it's your live backend server.

To confirm it's working, open a **second terminal** (click the `+` in the terminal panel)
and run:
```bash
curl http://localhost:8000/api/health
```
You should see `{"status":"ok", ...}`.

## Step 5: Start the frontend dashboard

1. Open a new (third) terminal.
2. Run:
   ```bash
   cd frontend
   cp .env.example .env
   npm run dev
   ```
3. Codespaces will show a popup offering to open the forwarded port (5173) in your
   browser. Click **Open in Browser**. That's your dashboard.
4. If the dashboard says it can't reach the backend: click the **Ports** tab at the bottom
   of the Codespace, find port `8000`, right-click it, choose **Port Visibility → Public**,
   then copy that forwarded URL and paste it into `frontend/.env` as `VITE_API_URL=<that
   URL>` (no trailing slash), then stop and re-run `npm run dev`.

## Step 6: Try it

On the dashboard's Overview page, click **"Simulate schema-drift incident."** This kicks
off the full seven-agent pipeline against the built-in demo scenario (an upstream schema
change that breaks a staging table, breaches a freshness SLA, and threatens an executive
dashboard). Watch the incident detail page to see each agent's reasoning trace, the
generated repair code, and (in demo mode) a "dry run" Pull Request link.

Or skip the dashboard entirely and watch it happen in the terminal:
```bash
python scripts/run_demo_incident.py
```

## Step 7 (optional): Connect a real GitHub repo so it opens real Pull Requests

1. Create a GitHub Personal Access Token (Settings → Developer settings → Personal access
   tokens → generate one with `repo` scope).
2. In `backend/.env`, set:
   ```
   GITHUB_TOKEN=your_token_here
   GITHUB_REPO=your-username/some-test-repo
   ```
3. Restart the backend terminal (Ctrl+C, then re-run the `uvicorn` command).
4. Now when the GitOps Agent runs, it'll open a real branch + commit + Pull Request in
   that repository instead of a dry-run message.

## Step 8 (optional): Connect a real DataHub instance via the MCP Server

This is only needed if you want to move beyond the demo dataset. PhoenixForge AI talks
to real DataHub through the official **DataHub MCP Server** (`mcp-server-datahub`) —
this is the hackathon's required agent-integration surface, so use this path (not the
GraphQL fallback) for anything you plan to submit.

1. Spin up DataHub locally with the Quickstart Guide linked on the hackathon's Resources
   page (or point at any DataHub instance you already have).
2. In `backend/.env`, set:
   ```
   DEMO_MODE=false
   INTEGRATION_MODE=mcp
   DATAHUB_GMS_URL=<your DataHub GMS URL>
   DATAHUB_TOKEN=<your DataHub personal access token>
   MCP_SERVER_COMMAND=uvx mcp-server-datahub@latest
   MCP_ENABLE_MUTATIONS=true
   ```
3. Make sure `uv` is available in the Codespace (`pip install uv --break-system-packages`
   if `uvx` isn't found) — the backend launches the MCP server itself as a subprocess,
   you don't need a separate terminal for it.
4. Restart the backend. Every agent keeps working unchanged — only `datahub_client.py`
   switches from reading `sample_data/mock_datahub_metadata.json` to calling the MCP
   Server's `search`, `get_lineage`, `list_schema_fields`, and (for write-back)
   `add_tags` / `update_description` / `save_document` tools.
5. If the MCP server can't start (DataHub unreachable, `uvx` missing, etc.), the backend
   automatically falls back to demo data for that call and prints a warning — it won't
   crash the pipeline, but fix the underlying issue before recording your demo video.

---

## Troubleshooting

- **"Could not reach the PhoenixForge AI backend"** on the dashboard → make sure the
  `uvicorn` terminal is still running, and that port 8000 is set to Public in the Ports tab.
- **Agent responses say "[LLM DISABLED]"** → you haven't set `ANTHROPIC_API_KEY` in
  `backend/.env`, or you need to restart the backend after adding it.
- **`pip install` fails** → add `--break-system-packages` to the command (Codespaces'
  Python is externally managed):
  ```bash
  pip install -r backend/requirements.txt --break-system-packages
  ```
- **Port 5173 shows a blank page** → hard refresh, or check the terminal running
  `npm run dev` for errors; usually means `npm install` didn't finish.
