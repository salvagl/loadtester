# Backend Dockerfile for LoadTester
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    UV_CACHE_DIR=/tmp/uv-cache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    sudo \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install K6 directly from GitHub releases
RUN wget -O k6.tar.gz "https://github.com/grafana/k6/releases/download/v0.47.0/k6-v0.47.0-linux-amd64.tar.gz" \
    && tar -xzf k6.tar.gz \
    && mv k6-v0.47.0-linux-amd64/k6 /usr/local/bin/ \
    && rm -rf k6.tar.gz k6-v0.47.0-linux-amd64/ \
    && chmod +x /usr/local/bin/k6

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Create app directory
WORKDIR /app

# Create directories for shared data
RUN mkdir -p /app/data \
             /app/shared/data/uploads \
             /app/shared/data/mocked \
             /app/shared/reports/generated \
             /app/k6_scripts \
             /app/k6_results

# Copy dependency files
COPY requirements.txt ./

# Install dependencies using pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy application code
COPY loadtester/ ./loadtester/

# Create non-root user and add to sudoers
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app && \
    echo "appuser ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# Create K6 config directory for appuser and set permissions
RUN mkdir -p /home/appuser/.config/loadimpact/k6 && \
    chown -R appuser:appuser /home/appuser/.config && \
    chmod -R 755 /home/appuser/.config
# Note: We don't switch to appuser here, the entrypoint script will handle it

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Set entrypoint and default command
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "loadtester.main:app", "--host", "0.0.0.0", "--port", "8000"]
