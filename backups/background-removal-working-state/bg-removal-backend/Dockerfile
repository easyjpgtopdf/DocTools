# Dockerfile for Background Removal Service with BiRefNet GPU
FROM python:3.11-slim

# Install system dependencies (including OpenCV dependencies)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libopencv-dev \
    python3-opencv \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download BiRefNet model (this will happen on first request, but we can pre-download)
# The model will be downloaded automatically by rembg on first use

# Copy application code
COPY app.py .

# Expose port
EXPOSE 8080

# Use gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "1", "--timeout", "300", "app:app"]

