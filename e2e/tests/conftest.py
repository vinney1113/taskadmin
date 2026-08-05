import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

ROOT = Path(__file__).resolve().parents[2]

DEFAULT_PROJECTS = [
    {"name": "Office Project", "icon": "briefcase"},
    {"name": "Personal Project", "icon": "user"},
    {"name": "Daily Study", "icon": "book"},
]


def _resolve_executable(env_var, candidates, default):
    env = os.environ.get(env_var)
    if env and Path(env).exists():
        return env
    for name in candidates:
        path = shutil.which(name)
        if path:
            return path
    return default


def resolve_chromium():
    return _resolve_executable(
        "CHROMIUM_BIN",
        ["chromium", "chromium-browser", "google-chrome", "google-chrome-stable"],
        "/usr/bin/chromium",
    )


def resolve_chromedriver():
    return _resolve_executable(
        "CHROMEDRIVER_BIN",
        ["chromedriver"],
        "/usr/bin/chromedriver",
    )


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def api_request(base_url, method, path, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        base_url + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read()
            return resp.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as err:
        return err.code, None


def reset_db(base_url):
    _, tasks = api_request(base_url, "GET", "/api/tasks")
    for task in tasks or []:
        api_request(base_url, "DELETE", f"/api/tasks/{task['id']}")
    _, projects = api_request(base_url, "GET", "/api/projects")
    for project in projects or []:
        api_request(base_url, "DELETE", f"/api/projects/{project['id']}")
    for project in DEFAULT_PROJECTS:
        api_request(base_url, "POST", "/api/projects", project)


@pytest.fixture(scope="session")
def base_url():
    port = _free_port()
    env = os.environ.copy()
    env["PORT"] = str(port)
    env.setdefault(
        "DATABASE_URL",
        "postgres://postgres@127.0.0.1:5432/taskadmin",
    )
    proc = subprocess.Popen(
        ["node", "server.js"],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    for _ in range(100):
        if proc.poll() is not None:
            raise RuntimeError("Express server exited during startup")
        try:
            urllib.request.urlopen(url + "/api/projects", timeout=1)
            break
        except Exception:
            time.sleep(0.1)
    else:
        raise RuntimeError("Express server did not start in time")
    yield url
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture(autouse=True)
def clean_db(base_url):
    reset_db(base_url)
    yield


@pytest.fixture
def driver(base_url):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.binary_location = resolve_chromium()
    service = Service(resolve_chromedriver())
    d = webdriver.Chrome(service=service, options=opts)
    d.set_page_load_timeout(30)
    d.get(base_url)
    yield d
    d.quit()


@pytest.fixture
def context():
    return {"created": {}, "colors": {}}
