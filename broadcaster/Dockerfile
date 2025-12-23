FROM python:3.12-slim

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Set workdir inside container
WORKDIR /app

# Install Python deps
RUN pip install --no-cache-dir nats-py aiohttp

# Default envs (override via deployment)
# ENV NATS_URL="nats://host.docker.internal:4222" \
#     SLACK_WEBHOOK_URL=""

# Copy code
COPY broadcaster.py .

# Run the broadcaster
CMD ["python", "broadcaster.py"]
