# ============================================
# Dockerfile for Google Cloud Run
# Background Remover with Rembg U²-Net Latest
# ============================================

# Use Python 3.10 slim image (better onnxruntime compatibility)
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for rembg and image processing
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements-cloudrun.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app-cloudrun.py app.py

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV REMBG_MODEL=u2net
# Fix for onnxruntime executable stack issue
ENV LD_PRELOAD=""
ENV MALLOC_CHECK_=0

# Expose port
EXPOSE 8080

# Run with gunicorn
# Note: Model will auto-download on first request (~180MB)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 2 --timeout 300 --max-requests 100 app:app
