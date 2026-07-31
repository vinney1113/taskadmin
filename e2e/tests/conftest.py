import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

ROOT = Path(__file__).resolve().parents[2]


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


@pytest.fixture(scope="session")
def base_url():
    port = _free_port()
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "http.server",
            str(port),
            "--bind",
            "127.0.0.1",
            "--directory",
            str(ROOT),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            urllib.request.urlopen(url, timeout=1)
            break
        except Exception:
            time.sleep(0.1)
    yield url
    proc.terminate()
    proc.wait()


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
