# ============================================
# Dockerfile for Google Cloud Run
# Background Remover with Pure PyTorch U2NetP
# Optimized for 4GB Memory, 2 CPU
# No ONNX - Cloud Run Compatible
# ============================================

FROM python:3.10-slim

WORKDIR /app

# Install system deps for image processing
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download U2Net Full pre-trained weights during build (if not already present)
# This ensures best quality results
RUN pip install --no-cache-dir gdown && \
    if [ ! -f u2net.pth ]; then \
        echo "Downloading U2Net Full weights (173 MB)..." && \
        python -m gdown https://drive.google.com/uc?id=1ao1ovG1Qtx4b7EoskHXmi2E9rp5CHLcZ -O u2net.pth && \
        echo "✅ Weights downloaded successfully"; \
    else \
        echo "✅ Weights file already present"; \
    fi

# Copy application code
COPY app.py .
COPY u2net_model.py .

# Clear Python cache
RUN find /app -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
RUN find /app -name "*.pyc" -delete 2>/dev/null || true

# Environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV MALLOC_CHECK_=0

# Expose port
EXPOSE 8080

# Run with gunicorn - single worker for stability, timeout 300s
# Concurrency: 1 (can be increased to 4 if needed)
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8080", "app:app", "--timeout", "300"]

