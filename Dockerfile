FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including procps for ps command
RUN apt-get update && apt-get install -y \
    cron \
    procps \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Ensure Python is accessible via multiple command names
RUN ln -sf /usr/local/bin/python /usr/local/bin/python3 \
    && ln -sf /usr/local/bin/python /usr/bin/python3 \
    && ln -sf /usr/local/bin/python /usr/bin/python

# Debug: Show Python installation status
RUN echo "=== Python Installation Debug ===" \
    && echo "Python version: $(python --version)" \
    && echo "Python3 version: $(python3 --version)" \
    && echo "Python location: $(which python)" \
    && echo "Python3 location: $(which python3)" \
    && echo "PATH: $PATH" \
    && ls -la /usr/local/bin/python* \
    && ls -la /usr/bin/python* \
    && echo "================================"

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

# Final verification that Python commands work
RUN python --version && python3 --version

# Set environment variables
ENV PYTHONPATH=/app/source
ENV PYTHONUNBUFFERED=1
ENV PATH=/usr/local/bin:/usr/bin:/bin

ENTRYPOINT ["./entrypoint.sh"]