FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY source/ ./source/
COPY templates/ ./templates/
COPY config/ ./config/
COPY entrypoint.sh .
COPY check_config.py .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create a non-root user with specific UID/GID
RUN groupadd -g 1000 emby && useradd -u 1000 -g emby -m emby

# Create necessary directories and set permissions
RUN mkdir -p /var/log \
    && chown -R emby:emby /app /var/log

# Switch to non-root user
USER emby

# Set environment variables
ENV PYTHONPATH=/app/source
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["./entrypoint.sh"]
    && chown -R emby:emby /app /var/log

# Switch to non-root user
USER emby

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["./entrypoint.sh"]