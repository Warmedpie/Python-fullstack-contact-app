"""
Production entry point.

Flask's own dev server (used by app.py when run directly) prints a
warning that it isn't meant for production use - no concurrency, no
process management, not hardened against slow/malicious clients. This
file serves the exact same app through Waitress instead, a pure-Python
WSGI server that has no OS-specific dependencies (unlike Gunicorn, which
relies on fork() and doesn't run on native Windows), so it's a drop-in
production runner on any platform this app might get deployed to.

Local development:
    python app.py            (Flask dev server, debug=True, auto-reload)

Production / deployment:
    python wsgi.py            (Waitress, host/port from Config)

HOST and PORT default to 0.0.0.0:8000 and can be overridden without code
changes via the CONTACTS_HOST / CONTACTS_PORT environment variables (see
config.py). CONTACTS_DB_PATH likewise overrides where the SQLite file
lives, e.g. for a persistent data directory in a deployment environment.
"""
from waitress import serve

from config import ProdConfig
from app import create_app

app = create_app(ProdConfig)

if __name__ == "__main__":
    host = app.config["HOST"]
    port = app.config["PORT"]
    print(f"Serving on http://{host}:{port} (Waitress)")
    serve(app, host=host, port=port)
