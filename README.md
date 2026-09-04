# SkillNova — Functional Hackathon MVP

A React + TypeScript frontend backed by FastAPI + SQLite. The core data loop is:

**User data → skill graph → skill gap → learning → readiness → opportunity matching → portfolio → application/research connection**

## Structure

- `backend/` — FastAPI, SQLAlchemy, SQLite, auth, skill-gap/readiness/matching logic, REST APIs
- `frontend/` — React + TypeScript + Vite role-based application

## Local development

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL, normally `http://localhost:5173`.

The backend automatically creates `skillnova.db` and seeds only reusable skills and role requirements. No fake student/company/academician account or fake scores are seeded.

## Demo

1. Register as Student.
2. Complete profile and choose a target role.
3. Add/edit skills with proficiency values.
4. See readiness, gaps and learning recommendations update from the same data.
5. Register a separate Company account and publish an opportunity with requirements such as `Python:80, SQL:75`.
6. Company candidate matching ranks the actual student account.
7. Student can view the portfolio and apply.
8. Register as Academician and publish research/project opportunities.
9. Register as Admin to see live platform counts and taxonomy.
