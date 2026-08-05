# AGENTS.md

## System Information

- **OS**: Alpine Linux v3.24
- **Kernel**: Linux 6.12.54-linuxkit aarch64
- **Package Manager**: apk (apk-tools 3.0.6-r0)
- **HTTP client**: Only BusyBox `wget` is available in this environment (no curl, python, node, or openssl).

## Figma API

- Base URL: `https://api.figma.com`
- Auth: send the personal access token via the `X-Figma-Token` header (the `Authorization: Bearer` variant returns `401 Unauthorized`).
- Token: keep it out of git; pass it via env var (e.g. `FIGMA_TOKEN`).
- Verified against `GET /v1/me` → `200 OK`, account "Vinay Kambli" (`vinney1113@gmail.com`, id `1666534423425936834`).
- Example: `wget -qS --spider --header="X-Figma-Token: $FIGMA_TOKEN" -O /dev/null https://api.figma.com/v1/me`

## Testing

- E2E tests use pytest-bdd (Gherkin) + Selenium against system Chromium (`chromium`/`chromedriver` via apk). Playwright is NOT available on this Alpine (musl) host.
- The app is now a full stack: `server.js` (Express) serves the static app and a JSON REST API backed by PostgreSQL. The e2e harness boots the Express server against the `taskadmin` database instead of a plain `http.server`. **Running the e2e suite requires Node.js and a running PostgreSQL server** (`postgresql18` via apk; init with `initdb -D /var/lib/postgresql/18/data -U postgres -A trust`, create DB `taskadmin`).
- Scenarios: `e2e/features/taskadmin.feature`, `specs/kanban/kanban.feature`, `specs/figma-design/figma-design.feature`, `specs/tasks-rest-api/tasks-rest-api.feature`; step definitions: `e2e/tests/test_taskadmin.py`; fixtures (auto-started Express server, DB reset per test, headless driver): `e2e/tests/conftest.py`.
- Run the API tests: `npm test` (Node built-in test runner + supertest against the `taskadmin` DB).
- Run all e2e tests: `e2e/.venv/bin/python -m pytest -v`
- Run a single test: `e2e/.venv/bin/python -m pytest "e2e/tests/test_taskadmin.py::test_edit_a_task_title" -v`
- The venv lives in `e2e/.venv` (installed from `e2e/requirements.txt`, ignored by git). If it's missing, recreate with: `python3 -m venv e2e/.venv && e2e/.venv/bin/pip install -r e2e/requirements.txt`
- Node dependencies install with `npm install` (creates `node_modules/`, gitignored).
- CI/CD: GitHub Actions (`.github/workflows/ci.yml`) runs `npm test` and the e2e suite on `ubuntu-latest` against a PostgreSQL service container, using Chrome for Testing + matching chromedriver (installed via `browser-actions/setup-chrome`). It deploys to GitHub Pages only if the tests pass on `main`. Browser/chromedriver paths can be overridden via `CHROMIUM_BIN`/`CHROMEDRIVER_BIN` env vars (see `e2e/tests/conftest.py`).
