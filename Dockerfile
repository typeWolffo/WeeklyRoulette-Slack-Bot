# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Create volume for database
RUN mkdir -p /data

# Set environment variables
ENV DATABASE_URL=sqlite:///data/weeklyroulette.db
ENV PYTHONPATH=/app/src

# Expose port (not really needed for Socket Mode but good practice)
EXPOSE 8080

# Run the application (matching local makefile setup)
CMD ["python", "-m", "main"]
