FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create reports directory
RUN mkdir -p reports && \
    chmod -R 777 reports

# Expose the port the app runs on
ENV PORT 8080
EXPOSE 8080

# Use gunicorn for production
CMD exec gunicorn --bind :$PORT app:app -w 4 -k uvicorn.workers.UvicornWorker --timeout 300 