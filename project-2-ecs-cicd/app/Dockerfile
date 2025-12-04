# Use a lightweight Python image
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Make Python a bit cleaner in containers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy dependency list and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app code
COPY . .

# Default port our app listens on
ENV PORT=8080

# Use gunicorn (production-style server)
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:8080", "--workers", "3"]

