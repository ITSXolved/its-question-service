FROM python:3.9-slim

WORKDIR /app

ENV PIP_DEFAULT_TIMEOUT=120

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=120 -r requirements.txt

# Copy application code
COPY app/ ./app/

# Set environment variables
ENV PYTHONPATH=/
ENV FLASK_APP=app/main.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Run application with explicit Python module path
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app.main:app"]