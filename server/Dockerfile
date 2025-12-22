# syntax=docker/dockerfile:1
FROM node:18-bullseye

# Install prerequisites, fonts, Python for rembg
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       wget \
       tar \
       ca-certificates \
       python3 \
       python3-pip \
       fonts-dejavu \
       fonts-liberation \
       fonts-noto \
       fonts-noto-cjk \
       fonts-noto-color-emoji \
       libreoffice \
       libreoffice-core \
       libreoffice-writer \
       libreoffice-calc \
       libreoffice-impress \
       libreoffice-base-core \
       libreoffice-java-common \
       python3-uno \
    && rm -rf /var/lib/apt/lists/*

# Install rembg (U²-Net background remover)
RUN pip3 install --no-cache-dir rembg==2.0.50

# Create non-root user for app runtime
RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /home/appuser/app

# Install Node dependencies
COPY package*.json ./
RUN npm install --omit=dev

# Copy server source
COPY . .

# Cloud Run automatically sets PORT environment variable
EXPOSE 8080

# Adjust ownership and drop privileges
RUN chown -R appuser:appuser /home/appuser/app
USER appuser

# Healthcheck for Render
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["npm", "start"]
