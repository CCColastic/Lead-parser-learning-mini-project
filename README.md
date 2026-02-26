# Lead Parser (Mini Project)

A small full-stack project that takes a free-form lead message (email/chat text), extracts structured lead data using a DeepSeek LLM call (via the OpenAI Python SDK with a custom `base_url`), and stores the interaction history in SQLite.

## Features

- **FastAPI backend**
  - `POST /api/extract` — extract structured lead JSON from text (LLM-powered)
  - `GET /api/history` — list recent interactions (includes parsed object + raw JSON string)
  - `DELETE /api/history` — clear all stored interactions (dev helper)
  - `GET /health` — health check
  - Rate limiting on `/api/extract` using **SlowAPI**
- **SQLite** persistence via **SQLModel**
- **React + Vite frontend**
  - Text input → extract → show result
  - Show history with parsed lead JSON
  - Clear history button
- Uses Vite dev proxy so the frontend can call `/api/*` without CORS hassle in dev.

---

## Project Structure

```
.
├─ backend/
│  ├─ app.py                # FastAPI app + routes
│  ├─ db.py                 # SQLite engine + session dependency
│  ├─ llm.py                # DeepSeek call + JSON parsing + retry
│  ├─ models.py             # SQLModel table + response schemas
│  ├─ requirements.txt
│  └─ data/                 # runtime sqlite db (ignored by git)
└─ frontend/
   ├─ src/App.jsx           # UI
   ├─ vite.config.js        # proxy to backend
   └─ package.json
```

---

## Requirements

- Python 3.10+ recommended
- Node.js 18+ recommended
- A DeepSeek API key

---

## Backend Setup (FastAPI)

### 1) Create and activate venv

From repo root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```powershell
pip install -r requirements.txt
```

### 3) Set environment variables

In the **same PowerShell session** where you will run `uvicorn`:

```powershell
$env:DEEPSEEK_API_KEY="YOUR_DEEPSEEK_KEY"
$env:DEEPSEEK_BASE_URL="https://api.deepseek.com"
$env:DEEPSEEK_MODEL="deepseek-chat"
```

Notes:
- `DEEPSEEK_BASE_URL` defaults to `https://api.deepseek.com` if not set.
- `DEEPSEEK_MODEL` defaults to `deepseek-chat` if not set.

### 4) Run the backend

```powershell
uvicorn app:app --reload --port 8000
```

Backend will create the SQLite DB at:

- `backend/data/app.db`

### 5) Backend Docs / Swagger UI

Open:

- http://127.0.0.1:8000/docs

---

## Frontend Setup (React + Vite)

### 1) Install dependencies

From repo root:

```powershell
cd frontend
npm install
```

### 2) Run the frontend

```powershell
npm run dev
```

Open:

- http://localhost:5173

The dev server proxies requests to the backend:
- `/api/*` → `http://127.0.0.1:8000/api/*`
- `/health` → `http://127.0.0.1:8000/health`

---

## API Endpoints

### `POST /api/extract`

Extract structured lead data from text (rate limited).

**Request**
```json
{
  "text": "Hi, I'm Sam from Acme. Email: sam@acme.com. Need a demo next week."
}
```

**Response**
```json
{
  "name": null,
  "email": "sam@acme.com",
  "phone": null,
  "company": "Acme",
  "request_summary": "…",
  "urgency": "medium"
}
```

If the rate limit is exceeded, returns `429 Too Many Requests`.

---

### `GET /api/history?limit=20`

Returns recent interactions (newest first). Each item includes:
- `parsed_json`: raw JSON string stored in DB (debug)
- `parsed`: parsed/validated object when available (frontend-friendly)

---

### `DELETE /api/history`

Deletes all interaction rows (development helper).

---

### `GET /health`

Simple health check:
```json
{ "ok": true }
```

---

## Development Notes

### Rate limiting
`/api/extract` is limited per IP (example: `5/minute`). You can tune it in `backend/app.py` where the decorator is applied:
- `@limiter.limit("5/minute")`

### SQLite location
The database is stored in `backend/data/app.db`. The `backend/data/` folder is ignored by git.

### Troubleshooting

**1) `sqlite3.OperationalError: no such table: interaction`**
- Ensure the app runs DB initialization at startup (lifespan).
- Ensure models are imported before `SQLModel.metadata.create_all(...)`.
- If needed, delete the DB file (`backend/data/app.db`) and restart the backend.

**2) `KeyError: 'DEEPSEEK_API_KEY'`**
- The env var must be set in the same terminal session that runs `uvicorn`.
- Stop the server, set env vars, then restart `uvicorn`.

**3) VS Code / Pylance: `Import "openai" could not be resolved`**
- Confirm VS Code is using `backend/.venv` as interpreter.
- Reinstall dependencies inside the venv: `pip install -r requirements.txt`.

---

## License

This is a learning mini-project; add a license if you plan to distribute it.