# Repository Guidelines

## Project Structure & Module Organization
Place the Django project under `backend/sales_inventory/` with feature apps (`accounts`, `products`, `orders`, `analytics`, `system`). Each app should expose models, services, and `tests/` packages. Put templates and Atomic components in `backend/templates/` and `backend/static/js/components/{atoms,molecules,organisms}`. Store media in `backend/media/`, CDN assets in `backend/static/cdn/`, and keep planning docs in `Documentation/`.

## Build, Test, and Development Commands
- `python -m venv .venv`: create the isolated runtime expected by all automation.
- `.venv\Scripts\activate`: activate the environment before installing or running anything.
- `pip install -r requirements.txt`: install Django, testing, and linting dependencies.
- `python manage.py migrate`: apply schema changes against the MySQL instance.
- `python manage.py runserver 0.0.0.0:8000`: serve the kiosk, POS, and admin interfaces locally.
- `python manage.py collectstatic --noinput`: bundle static assets before releasing.

## Coding Style & Naming Conventions
Follow PEP 8 with four-space indentation, type annotations on public functions, `snake_case` modules, `CamelCase` models, and lowercase template names. Run `black` and `isort` before committing, keep imports grouped (stdlib, third party, local), and mirror the Atomic Design hierarchy by naming atoms `btn-*.js`, molecules `order-card.js`, and organisms `pos-dashboard.js`.

## Testing Guidelines
Use `pytest` (wired through Django) for unit and integration coverage; add a `tests/` package to every app with files named `test_<feature>.py`. Run `pytest --cov=backend` before each pull request, keep fixtures in `tests/fixtures/`, and cover HTMX or Alpine flows with request tests that assert rendered component states.

## Commit & Pull Request Guidelines
The repository has no history yet, so adopt Conventional Commits (`feat:`, `fix:`, `chore:`) and scope changes by app name when possible. Keep subjects imperative and under 72 characters. Pull requests should describe the change, link planning issues, list migrations, attach relevant screenshots or terminal captures, and request at least one review.

## Security & Configuration Tips
Store secrets such as database passwords and API keys in `.env` files and reference them through `settings.py` using `os.environ`. Never commit `.env`, database dumps, or collected static artefacts. Use separate settings modules for development and production, enforce HTTPS redirects before deployment, and validate that audit logging stays enabled whenever cashier or admin flows are touched.
