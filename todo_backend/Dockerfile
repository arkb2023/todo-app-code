FROM python:3.12-slim

# Set work directory
WORKDIR /app

COPY app/ ./app/

RUN apt-get update && apt-get install -y gcc libpq-dev netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

ENV PORT=3000

# Default startup command
#CMD ["./wait-for-it.sh", "db", "5432", "--", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
ENTRYPOINT ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]