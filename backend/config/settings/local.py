"""
RumahAsri — Local Development Settings
"""

from decouple import config

from .base import *  # noqa

# ── Debug ─────────────────────────────────────────────────────
DEBUG = config("DEBUG", default=True, cast=bool)

# ── Database — SQLite for local dev (zero config!!) ───────────
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
