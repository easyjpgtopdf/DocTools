# Use Python 3.11 slim as base image
# Build timestamp: 2025-12-28T11:30:00Z - Force cache invalidation for GEOMETRIC_HYBRID mode + Form Parser fix
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py ./
COPY free_pdf_to_excel/ ./free_pdf_to_excel/
COPY free_heuristic/ ./free_heuristic/
COPY premium_layout/ ./premium_layout/

# Expose port
EXPOSE 8080

# Set environment variable
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

