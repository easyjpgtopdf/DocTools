.PHONY: install run test docker-build docker-run deploy clean

# Variables
PYTHON := python3
PIP := pip3
DOCKER_IMAGE := pdf-to-word-backend
PROJECT_ID := $(shell echo $$PROJECT_ID)
SERVICE_NAME := pdf-to-word-converter
REGION := us-central1

# Install dependencies
install:
	$(PIP) install -r requirements.txt

# Run locally
run:
	uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Run tests
test:
	pytest tests/ -v

# Build Docker image
docker-build:
	docker build -t $(DOCKER_IMAGE) .

# Run Docker container
docker-run:
	docker run -p 8080:8080 --env-file .env $(DOCKER_IMAGE)

# Deploy to Cloud Run
deploy:
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "Error: PROJECT_ID not set"; \
		exit 1; \
	fi
	docker build -t gcr.io/$(PROJECT_ID)/$(SERVICE_NAME) ./backend
	docker push gcr.io/$(PROJECT_ID)/$(SERVICE_NAME)
	gcloud run deploy $(SERVICE_NAME) \
		--image gcr.io/$(PROJECT_ID)/$(SERVICE_NAME) \
		--platform managed \
		--region $(REGION) \
		--allow-unauthenticated \
		--memory 2Gi \
		--cpu 2 \
		--timeout 540

# Clean up
clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

