"""
Shared harness for the Playwright end-to-end suite.

This is deliberately different from tests/ (which mocks every dependency
and never touches a real database): these tests drive a real Chromium
browser against the real Flask app - the same create_app() factory
app.py and wsgi.py use - backed by a real, temporary SQLite file. They
exist to catch the class of bug the mocked unit tests structurally
can't: broken DOM wiring, CSS that never actually reveals a button,
JS/HTML selector drift, or a click that doesn't do what the code assumes
it does. Two of the bugs fixed earlier in this project (Cancel reverting
fields to blank instead of the saved values, and "+" silently pre-filling
the previous contact's name) were only caught this way.

Each TestCase class gets its OWN server subprocess on its own free port,
and its own throwaway SQLite file, created in setUpClass and torn down in
tearDownClass. That's what makes these safe to re-run and to run in any
order: nothing a previous class did (contacts it created, etc.) can leak
into another class's assertions like "the list starts empty". Within a
class, tests are named test_01_..., test_02_... and share one browser
page across the whole class, because each file is really one continuous
UI flow (select a contact, edit it, cancel, delete it) rather than a set
of independent unit tests - splitting each step into a fully isolated
test would mean re-deriving all the earlier steps' state every time.
"""
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request

from playwright.sync_api import sync_playwright

_SERVER_RUNNER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_server_runner.py")


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class E2ETestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fd, cls.db_path = tempfile.mkstemp(suffix=".db", prefix="contacts_e2e_")
        os.close(fd)
        os.remove(cls.db_path)  # init_db() recreates it fresh on server startup

        cls.port = _free_port()
        cls.base_url = f"http://127.0.0.1:{cls.port}"

        log_fd, cls._log_path = tempfile.mkstemp(suffix=".log", prefix="contacts_e2e_server_")

        env = os.environ.copy()
        env["CONTACTS_DB_PATH"] = cls.db_path
        env["CONTACTS_HOST"] = "127.0.0.1"
        env["CONTACTS_PORT"] = str(cls.port)

        cls.server = subprocess.Popen(
            [sys.executable, _SERVER_RUNNER],
            env=env,
            stdout=log_fd,
            stderr=subprocess.STDOUT,
        )
        os.close(log_fd)  # the child keeps its own inherited copy

        try:
            cls._wait_for_server()
        except Exception:
            cls._fail_with_server_log()
            raise

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()
        # clipboard permissions are only exercised by the copy-button
        # tests, but granting them for every class is harmless.
        cls.context = cls.browser.new_context(permissions=["clipboard-read", "clipboard-write"])
        cls.page = cls.context.new_page()
        cls.page.goto(cls.base_url, wait_until="networkidle")

    @classmethod
    def _wait_for_server(cls, timeout=10):
        deadline = time.time() + timeout
        last_err = None
        while time.time() < deadline:
            if cls.server.poll() is not None:
                raise RuntimeError(
                    f"Server process exited early with code {cls.server.returncode}"
                )
            try:
                urllib.request.urlopen(f"{cls.base_url}/health", timeout=1)
                return
            except Exception as e:
                last_err = e
                time.sleep(0.2)
        raise RuntimeError(f"Server on {cls.base_url} never came up: {last_err}")

    @classmethod
    def _fail_with_server_log(cls):
        cls.server.terminate()
        try:
            with open(cls._log_path) as f:
                log = f.read()
        except OSError:
            log = "(could not read server log)"
        print(f"\n--- {cls.__name__} server log ---\n{log}\n--- end server log ---\n")

    @classmethod
    def tearDownClass(cls):
        cls.context.close()
        cls.browser.close()
        cls.playwright.stop()

        cls.server.terminate()
        try:
            cls.server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            cls.server.kill()
            cls.server.wait(timeout=5)

        for path in (cls.db_path, cls._log_path):
            if os.path.exists(path):
                os.remove(path)

    # ---- small helpers shared across the individual test files ----

    def is_hidden(self, selector):
        return self.page.eval_on_selector(selector, "el => el.classList.contains('hidden')")

    def opacity_of(self, selector):
        return self.page.eval_on_selector(selector, "el => getComputedStyle(el).opacity")

    def pointer_events_of(self, selector):
        return self.page.eval_on_selector(selector, "el => getComputedStyle(el).pointerEvents")

    def contact_count(self):
        return self.page.eval_on_selector_all(".contact-list-item", "els => els.length")

    def contact_list_texts(self):
        return self.page.eval_on_selector_all(
            ".contact-list-item", "els => els.map(el => el.textContent)"
        )

    def error_hidden(self):
        return self.is_hidden("#form-error")

    def error_text(self):
        return self.page.inner_text("#form-error")

    def make_contact(self, first, last):
        self.page.click("#add-contact-btn")
        self.page.fill("#first-name", first)
        self.page.fill("#last-name", last)
        with self.page.expect_response(
            lambda r: r.url.endswith("/api/contacts") and r.request.method == "POST"
        ):
            self.page.click("#save-btn")
        self.page.wait_for_timeout(400)
