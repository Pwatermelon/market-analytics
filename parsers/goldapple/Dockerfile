FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY goldapple/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps

# Copy parser code and common module
COPY goldapple/ ./goldapple/
COPY common/ ./common/

# Set Python path to include the parent directory
ENV PYTHONPATH=/app

# Run the service
CMD ["uvicorn", "goldapple.main:app", "--host", "0.0.0.0", "--port", "8003"] 