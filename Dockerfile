FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (if any needed for pandas/numpy builds)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app/src

COPY src ./src
COPY tests ./tests
COPY KIS ./KIS

CMD ["python", "src/main.py"]
