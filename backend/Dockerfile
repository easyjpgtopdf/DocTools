# Use Python 3.11 slim as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including LibreOffice and fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer \
    libreoffice-common \
    libreoffice-core \
    fonts-dejavu-core \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    fonts-liberation \
    fonts-liberation2 \
    poppler-utils \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Ensure soffice is in PATH
ENV PATH="/usr/bin:${PATH}"

# Download and install Krutidev and Chanakya fonts (if available)
# Note: These fonts may need to be manually added or downloaded from official sources
RUN mkdir -p /usr/share/fonts/truetype/hindi-fonts || true

# Note: For Krutidev/Chanakya fonts, you may need to:
# 1. Download fonts from official sources
# 2. COPY font files to Docker image
# 3. Run fc-cache to refresh font cache

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 8080

# Set environment variable
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Run the application
# PORT is automatically set by Cloud Run, use it via environment variable
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
