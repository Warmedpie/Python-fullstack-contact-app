"""
Standalone process launched by tests/e2e/base.py - not meant to be run by
hand (see run_test_server.py for a manual dev-server-on-a-fixed-port).

Boots the real app via the exact same create_app() factory app.py and
wsgi.py both use, reading DATABASE_PATH/HOST/PORT from the
CONTACTS_DB_PATH/CONTACTS_HOST/CONTACTS_PORT environment variables that
config.py already supports. base.py sets those to a throwaway port and a
throwaway SQLite file per test class, so this is a real server and a real
(temporary) database, not a mock of either.
"""
import os
import sys

# This file lives at tests/e2e/_server_runner.py, so the repo root
# (where config.py and app.py live) is three directories up.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _REPO_ROOT)

from config import Config
from app import create_app

if __name__ == "__main__":
    app = create_app(Config)
    app.run(
        host=app.config["HOST"],
        port=app.config["PORT"],
        debug=False,
        use_reloader=False,
    )
