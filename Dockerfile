FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including procps for ps command
RUN apt-get update && apt-get install -y \
    cron \
    procps \
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
RUN mkdir -p /var/log /var/spool/cron/crontabs \
    && chmod 0755 /var/spool/cron \
    && chmod 0755 /var/spool/cron/crontabs \
    && chown -R emby:emby /app /var/log

# Set environment variables
ENV PYTHONPATH=/app/source
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["./entrypoint.sh"]