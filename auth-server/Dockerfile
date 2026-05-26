FROM python:3.12-slim

# gcc + libffi-dev are required to compile the bcrypt C extension
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies in a separate layer so pip cache survives source changes
COPY auth-server/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Application source
COPY auth-server/ .

# Repo-level files needed by entrypoint (alembic + seed)
COPY alembic.ini .
COPY migrations/ migrations/
COPY scripts/seed.py scripts/seed.py

RUN chmod +x entrypoint.sh \
 && adduser --disabled-password --gecos "" appuser \
 && chown -R appuser:appuser /app

USER appuser

CMD ["/app/entrypoint.sh"]
