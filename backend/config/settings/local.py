"""
RumahAsri — Local Development Settings

DATABASE_URL env var is read when present (CI / staging).
Falls back to SQLite when not set (normal local dev — zero config).
"""

import os

from decouple import config

from .base import *  # noqa

# ── Debug ─────────────────────────────────────────────────────
DEBUG = config("DEBUG", default=True, cast=bool)

# ── Database ──────────────────────────────────────────────────
# CI sets DATABASE_URL (Postgres). Local dev uses SQLite by default.
_database_url = os.environ.get("DATABASE_URL")

if _database_url:
    # Parse postgres://user:pass@host:port/dbname
    import re
    _match = re.match(
        r"postgres://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)/(?P<name>.+)",
        _database_url,
    )
    if not _match:
        raise ValueError(f"Cannot parse DATABASE_URL: {_database_url}")
    DATABASES = {
        "default": {
            "ENGINE":   "django.db.backends.postgresql",
            "NAME":     _match.group("name"),
            "USER":     _match.group("user"),
            "PASSWORD": _match.group("password"),
            "HOST":     _match.group("host"),
            "PORT":     _match.group("port"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME":   BASE_DIR / "db.sqlite3",
        }
    }

# ── CORS — allow all in local dev ────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True

# ── Email — print to console in dev ──────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"