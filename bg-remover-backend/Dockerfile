# ============================================
# Dockerfile for Google Cloud Run
# Background Remover with Rembg U²-Net Latest
# ============================================

# Use Python 3.9 slim image (better onnxruntime compatibility, avoids executable stack issue)
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for rembg and image processing
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    binutils \
    util-linux \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements-cloudrun.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Fix onnxruntime executable stack issue - clear the executable stack flag
RUN find /usr/local/lib/python3.9/site-packages/onnxruntime -name "*.so" -exec execstack -c {} \; 2>/dev/null || true

# Note: onnxruntime executable stack issue - using environment variable workaround instead of execstack
# The execstack command was causing file corruption, so we skip it and rely on runtime environment

# Copy application code
COPY app-cloudrun.py app.py

# Clear Python cache to avoid any corrupted .pyc files
RUN find /app -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
RUN find /app -name "*.pyc" -delete 2>/dev/null || true

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV REMBG_MODEL=u2net
# Fix for onnxruntime executable stack issue
# Use setarch to allow executable stack (workaround for onnxruntime)
ENV LD_PRELOAD=""
ENV MALLOC_CHECK_=0
ENV ALLOW_EXECSTACK=1

# Expose port
EXPOSE 8080

# Run with gunicorn
# Note: Model will auto-download on first request (~180MB)
# Python 3.9 + onnxruntime 1.16.3 should work without setarch
CMD exec gunicorn --bind :$PORT --workers 1 --threads 2 --timeout 300 --max-requests 100 app:app
