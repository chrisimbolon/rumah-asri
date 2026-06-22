# ─────────────────────────────────────────────────────────────
#  DevelopIndo — Backend Dockerfile
#  Django 6 + Gunicorn, Python 3.12-slim
#  Mirrors kla Dockerfile pattern
# ─────────────────────────────────────────────────────────────

FROM python:3.12-slim

# Don't write .pyc files, don't buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ── System dependencies ───────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ───────────────────────────────────────
COPY requirements/base.txt requirements/base.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements/base.txt \
    && pip install --no-cache-dir gunicorn==21.2.0

# ── App source ────────────────────────────────────────────────
COPY . .

# ── Gunicorn ──────────────────────────────────────────────────
# 3 workers — right-sized for a single DigitalOcean droplet
# Timeout 120s — handles slow DB queries on first cold start
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
