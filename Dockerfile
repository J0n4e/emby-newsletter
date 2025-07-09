FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including cron, procps, and tzdata
RUN apt-get update && apt-get install -y \
    cron \
    procps \
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set timezone during build
ENV TZ=Europe/Bucharest
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Verify installations
RUN which cron && cron --version && echo "Cron installed successfully"
RUN python --version && echo "Python installed successfully"

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

# Create necessary directories and set permissions
RUN mkdir -p /var/log /var/spool/cron/crontabs \
    && chmod 0755 /var/spool/cron \
    && chmod 0755 /var/spool/cron/crontabs

# Set environment variables
ENV PYTHONPATH=/app/source
ENV PYTHONUNBUFFERED=1
ENV PATH=/usr/local/bin:/usr/bin:/bin

ENTRYPOINT ["./entrypoint.sh"]