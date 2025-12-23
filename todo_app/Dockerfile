FROM python:3.11-slim

WORKDIR /app

# System packages
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

ENV PORT=3000
ENV CACHE_DIR=/usr/src/app/files/cache
ENV TODO_BACKEND_URL=http://localhost:8081

ENTRYPOINT ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
