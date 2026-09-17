"""Application configuration."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    """Base configuration."""

    # DATABASE_PATH, HOST and PORT can be overridden with environment
    # variables at deploy time without touching code - e.g. pointing
    # production at a different data directory or port.
    DATABASE_PATH = os.environ.get(
        "CONTACTS_DB_PATH", os.path.join(BASE_DIR, "src", "data", "app.db")
    )
    FRONTEND_DIR = os.path.join(BASE_DIR, "Frontend")
    HOST = os.environ.get("CONTACTS_HOST", "0.0.0.0")
    PORT = int(os.environ.get("CONTACTS_PORT", "8000"))
    DEBUG = False


class DevConfig(Config):
    DEBUG = True


class TestConfig(Config):
    DATABASE_PATH = ":memory:"
    TESTING = True


class ProdConfig(Config):
    """Used by wsgi.py when running under a production WSGI server
    (Waitress) instead of Flask's built-in development server."""

    DEBUG = False
