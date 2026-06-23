FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/ src/
COPY tests/ tests/
COPY pytest.ini* setup.cfg* pyproject.toml* ./

# Default: run test suite
CMD ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]
