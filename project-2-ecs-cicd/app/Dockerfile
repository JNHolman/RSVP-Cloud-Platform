FROM python:3.12.15-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system app \
    && adduser --system --ingroup app app

RUN python -c "from urllib.request import urlretrieve; urlretrieve('https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem', '/app/rds-ca.pem')"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py demo.sql ./
RUN python -c "import sqlite3; from pathlib import Path; db = sqlite3.connect('demo.sqlite'); db.executescript(Path('demo.sql').read_text()); db.close()"

USER app
EXPOSE 8080

CMD ["gunicorn", "app:app", "-b", "0.0.0.0:8080", "--workers", "3", "--access-logfile", "-", "--error-logfile", "-"]
