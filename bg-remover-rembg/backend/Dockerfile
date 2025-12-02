# ============================================
# Dockerfile for Google Cloud Run
# Background Remover with Rembg U2Net
# Optimized for 2-4GB memory, 1-2 CPU
# Always Warm (min-instances: 1)
# ============================================

FROM python:3.10-slim

WORKDIR /app

# Install system deps for Pillow, onnxruntime
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Clear Python cache
RUN find /app -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
RUN find /app -name "*.pyc" -delete 2>/dev/null || true

# Environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Run with gunicorn - single worker for stability, timeout 300s
# Concurrency: 1 (can be increased to 4 if needed)
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8080", "app:app", "--timeout", "300"]

