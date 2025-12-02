# ============================================
# Dockerfile for Google Cloud Run V2 Alternative
# Background Remover - No onnxruntime
# Uses PIL + scikit-image
# 8GB Memory, 4 CPU Optimized
# ============================================

FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements-alternative.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app-alternative.py app.py

# Clear Python cache
RUN find /app -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
RUN find /app -name "*.pyc" -delete 2>/dev/null || true

# Environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV MALLOC_CHECK_=0

# Expose port
EXPOSE 8080

# Run with gunicorn (optimized for 4 CPU, 8GB memory)
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 300 --max-requests 1000 --worker-class sync app:app

