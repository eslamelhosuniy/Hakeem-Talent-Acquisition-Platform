FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install curl for healthchecks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy common directory
COPY common /app/common

# Copy semantic-matching service
COPY semantic-matching /app/semantic-matching

# Copy and install requirements
COPY semantic-matching/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app/semantic-matching

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

