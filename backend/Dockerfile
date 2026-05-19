FROM python:3.11-slim

# Install necessary system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Ensure data directory exists for SQLite & FAISS
RUN mkdir -p data

# Default Environment Variables
ENV APP_ENV=production
ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Start Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
