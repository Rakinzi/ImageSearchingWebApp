# Repository Guidelines

## Project Structure & Module Organization
- `backend/` holds the Flask API: `api/v1` & `api/v2` blueprints, `services/` logic, `models/` SQLAlchemy entities, `tasks/` Celery jobs, and `templates/` plus `static/` assets. Utility scripts live in `scripts/`; keep `chroma_db/` and `logs/` untracked.
- `frontend/` is the Vue 3 + Vite client with views in `src/views`, components in `src/components`, state in `src/stores`, API helpers in `src/services`, and routing in `src/router`.
- Docker compose files in `backend/` provision PostgreSQL, Redis, RabbitMQ, and Celery.

## Build, Test, and Development Commands
- `docker-compose -f backend/docker-compose.simple.yml up --build -d` launches the backend stack; use `restart app` after code-only edits and `logs -f app` for live output.
- Local Python work: create a virtualenv, `pip install -r backend/requirements.txt`, then run `flask db upgrade` through `docker-compose ... exec --user root app` when models change.
- In `frontend/`, run `npm install`, `npm run dev` for port 5173, `npm run build` for production assets, and `npm run preview` to verify the bundle.

## Coding Style & Naming Conventions
- Backend code targets Python 3.11; follow PEP 8, 4-space indents, snake_case modules/functions, PascalCase models, and add type hints at service boundaries.
- Vue single-file components stay in PascalCase, composables and stores in camelCase filenames, and Tailwind classes remain inline unless a utility is reused; refresh OpenAPI metadata with route edits.

## Testing Guidelines
- Backend tests run with `pytest`; place suites under `backend/tests/` mirroring modules and run `pytest --cov=. --cov-report=html` before review.
- Smoke-check with `curl http://localhost:5000/health` or the Flask test client, and isolate external integrations with fakes to stay deterministic.
- Coordinate before adding frontend testing; if Vitest or Cypress is introduced, expose it via `npm run test` and document fixtures.

## Commit & Pull Request Guidelines
- Write commits in the imperative present (`Add face crop fallback`), keep changes scoped, and include schema or asset updates the code depends on.
- PRs should note the problem, solution, and any Docker, migration, or feature-toggle impact; attach screenshots or cURL snippets for UI/API changes and link tracked issues.
- Validate `docker-compose ... up`, migrations, and `npm run build` locally so reviewers inherit a stable baseline.

## Security & Configuration Tips
- Copy `.env.example` to `.env`, customize secrets locally, and keep environment files out of version control (see `CONFIGURATION.md`).
- Rotate API keys through secret stores instead of committing them, and use `config/` factories to bind environment-specific settings.
