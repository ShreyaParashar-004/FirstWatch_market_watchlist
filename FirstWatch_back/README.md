# Watch API

Market-intelligence backend. Tracking = what already changed. Signals = what may start to matter.

Default providers are mocks. Do not enable real providers unless needed.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://127.0.0.1:8000/docs

## Tests

```powershell
.\.venv\Scripts\python -m pytest -q
```

## Auth for Lovable

1. `POST /api/auth/register` `{ "email", "password" }` → `{ "access_token" }`
2. Header: `Authorization: Bearer <access_token>`
