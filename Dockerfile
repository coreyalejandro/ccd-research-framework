# Dockerfile for CCD Research Framework
# Table Stakes Enhancement #5: Docker Container for Environment Replication

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt requirements.lock* ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data/synthetic data/control_group data/held_out output

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port for dashboard (if running web service)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command: run full pipeline
CMD ["python", "scripts/run_full_pipeline.py"]

# Alternative commands:
# Run tests: docker run ccd-framework pytest tests/
# Run detector: docker run ccd-framework python -m src.detector.proactive_detector
# Interactive shell: docker run -it ccd-framework /bin/bash

# Made with Bob
