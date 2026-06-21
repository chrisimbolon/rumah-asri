"""
DevelopIndo — Local Development Settings

DATABASE_URL env var switches between Postgres (CI / local Postgres)
and SQLite (zero-config fallback if DATABASE_URL is not set).

Current local setup: Postgres 15 via DATABASE_URL in .env
CI setup: Postgres 16 via DATABASE_URL in ci.yml
"""

import re

from decouple import config

from .base import *  # noqa

# ── Debug ─────────────────────────────────────────────────────
DEBUG = config("DEBUG", default=True, cast=bool)

# ── Database ──────────────────────────────────────────────────
# config() reads from .env file AND shell environment (shell wins)
# os.environ.get() only reads shell — misses .env file entirely
_database_url = config("DATABASE_URL", default="")

if _database_url.startswith("postgres://") or _database_url.startswith("postgresql://"):
    _match = re.match(
        r"postgres(?:ql)?://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)/(?P<name>.+)",
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
            "OPTIONS": {
                "connect_timeout": 10,
            },
        }
    }
else:
    # Zero-config fallback — SQLite for quick local dev without Postgres
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