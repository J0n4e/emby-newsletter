FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including procps for ps command
RUN apt-get update && apt-get install -y \
    cron \
    procps \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Debug: Show Python installation
RUN echo "=== Python Debug Info ===" && \
    (which python || echo "python not found") && \
    (which python3 || echo "python3 not found") && \
    (ls -la /usr/local/bin/python* || echo "No python in /usr/local/bin") && \
    (ls -la /usr/bin/python* || echo "No python in /usr/bin") && \
    (python --version || echo "python command failed") && \
    echo "========================="

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

# Create symlinks for python commands to ensure they're available
RUN (ln -sf /usr/local/bin/python /usr/local/bin/python3 || true) && \
    (ln -sf /usr/local/bin/python /usr/bin/python || true) && \
    (ln -sf /usr/local/bin/python /usr/bin/python3 || true)

# Final debug: Verify Python is accessible
RUN echo "=== Final Python Check ===" && \
    (python --version || echo "python command failed") && \
    (python3 --version || echo "python3 symlink missing") && \
    (which python || echo "python not in PATH") && \
    echo "========================="

# Important: Don't switch to non-root user since cron needs root permissions
# USER emby

# Set environment variables
ENV PYTHONPATH=/app/source
ENV PYTHONUNBUFFERED=1
ENV PATH=/usr/local/bin:/usr/bin:/bin

ENTRYPOINT ["./entrypoint.sh"]