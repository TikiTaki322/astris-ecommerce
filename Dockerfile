# syntax=docker/dockerfile:1

###### 1. BUILDER IMAGE (dependency assembly)
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies (only needed for assembly Python-packages e.g. psycopg2, Pillow, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install Python-dependencies into detached directory
RUN pip install --upgrade pip && \
    pip install --prefix=/builder-packages -r requirements.txt

###### 2. RUNTIME IMAGE (pure and light)
FROM python:3.12-slim

WORKDIR /app

# Copy dependency from builder-image
COPY --from=builder /builder-packages /usr/local

# Least system libraries set for postgres/pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . .

# Disable writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["gunicorn", "doom_market.wsgi:application", "--bind", "0.0.0.0:8000"]