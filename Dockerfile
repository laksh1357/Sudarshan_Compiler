# Production Dockerfile for Sudarshan Compiler Studio Backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source and backend code
COPY src/ ./src/
COPY backend/ ./backend/
COPY examples/ ./examples/

EXPOSE 8000

ENV PYTHONPATH=/app/src:/app

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
