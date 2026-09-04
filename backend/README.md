# SkillNova Backend

FastAPI + SQLAlchemy + SQLite MVP API.

## Run

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The database `skillnova.db` is created automatically and only seeds reusable skill taxonomy + role requirements; it does not seed a fake user.
