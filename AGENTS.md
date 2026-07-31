# AGENTS.md

## System Information

- **OS**: Alpine Linux v3.24
- **Kernel**: Linux 6.12.54-linuxkit aarch64
- **Package Manager**: apk (apk-tools 3.0.6-r0)

## Testing

- E2E tests use pytest-bdd (Gherkin) + Selenium against system Chromium (`chromium`/`chromedriver` via apk). Playwright is NOT available on this Alpine (musl) host.
- Scenarios: `e2e/features/taskadmin.feature`; step definitions: `e2e/tests/test_taskadmin.py`; fixtures (auto-started local server, headless driver): `e2e/tests/conftest.py`.
- Run all tests: `e2e/.venv/bin/python -m pytest -v`
- Run a single test: `e2e/.venv/bin/python -m pytest "e2e/tests/test_taskadmin.py::test_edit_a_task_title" -v`
- The venv lives in `e2e/.venv` (installed from `e2e/requirements.txt`, ignored by git). If it's missing, recreate with: `python3 -m venv e2e/.venv && e2e/.venv/bin/pip install -r e2e/requirements.txt`
