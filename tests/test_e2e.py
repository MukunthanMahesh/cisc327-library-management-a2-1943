import multiprocessing
import time
import urllib.error
import urllib.request
from contextlib import closing
from typing import Generator

import pytest
from playwright.sync_api import sync_playwright

from app import create_app


# Tests run using 'pytest tests/test_e2e.py'

def _run_flask_app(port: int) -> None:
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


def _wait_for_server(base_url: str, timeout_seconds: float = 10.0) -> None:
    start_time = time.time()
    url = f"{base_url}/catalog"

    while time.time() - start_time < timeout_seconds:
        try:
            with closing(urllib.request.urlopen(url, timeout=0.5)):
                return
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.2)

    raise RuntimeError("Flask server did not start within timeout.")


@pytest.fixture(scope="session")
def live_server() -> Generator[str, None, None]:
    port = 5001
    base_url = f"http://127.0.0.1:{port}"
    process = multiprocessing.Process(target=_run_flask_app, args=(port,), daemon=True)
    process.start()

    try:
        _wait_for_server(base_url)
        yield base_url
    finally:
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)


def _add_book_via_ui(base_url: str, title: str, author: str, isbn: str, total_copies: int = 3) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(60000)

        page.goto(f"{base_url}/add_book")

        page.fill("input#title", title)
        page.fill("input#author", author)
        page.fill("input#isbn", isbn)
        page.fill("input#total_copies", str(total_copies))

        page.get_by_role("button", name="Add Book to Catalog").click()

        page.wait_for_url("**/catalog")

        page.wait_for_selector(".flash-success")
        assert title in page.text_content("body")

        browser.close()


def test_add_book_appears_in_catalog(live_server: str) -> None:
    timestamp = int(time.time() * 1000)
    unique_isbn = f"9{timestamp:012d}"
    title = "E2E Flow 1 Test Book"
    author = "Test Author"

    _add_book_via_ui(live_server, title, author, unique_isbn, total_copies=4)


def test_borrow_book_from_catalog(live_server: str) -> None:
    timestamp = int(time.time() * 1000)
    unique_isbn = f"8{timestamp:012d}"
    title = "Playwright Borrowable Book"
    author = "Borrow Test Author"
    patron_id = f"{timestamp % 900000 + 100000:06d}"

    _add_book_via_ui(live_server, title, author, unique_isbn, total_copies=2)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(60000)

        page.goto(f"{live_server}/catalog")
        page.wait_for_selector("input[name='patron_id']")

        patron_input = page.locator("input[name='patron_id']").first
        patron_input.fill(patron_id)
        page.get_by_role("button", name="Borrow").first.click()

        page.wait_for_url("**/catalog")
        page.wait_for_selector(".flash-success, .flash-error")

        body_text = page.text_content("body")
        assert "Successfully borrowed" in body_text

        browser.close()
