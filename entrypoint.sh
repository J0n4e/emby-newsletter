#!/bin/bash

# Check if config file exists
if [ ! -f "/app/config/config.yml" ]; then
    echo "Error: Config file not found at /app/config/config.yml"
    echo "Please mount your config file to /app/config/config.yml"
    echo "Example: docker run -v ./config:/app/config ghcr.io/j0n4e/emby-newsletter"
    exit 1
fi

# Test configuration first
echo "Testing configuration..."
cd /app && python3 check_config.py -c /app/config/config.yml --no-connectivity

if [ $? -ne 0 ]; then
    echo "Configuration validation failed. Please check your config file."
    exit 1
fi

# Read the scheduler configuration
SCHEDULER_ENABLED=$(python3 -c "
import yaml
import sys
try:
    with open('/app/config/config.yml', 'r') as f:
        config = yaml.safe_load(f)
    scheduler = config.get('scheduler', {})
    print('true' if scheduler and 'cron' in scheduler else 'false')
except Exception as e:
    print('false', file=sys.stderr)
    print(f'Error reading scheduler config: {e}', file=sys.stderr)
")

# If scheduler is enabled, set up cron job
if [ "$SCHEDULER_ENABLED" = "true" ]; then
    echo "Setting up scheduled newsletter..."

    # Extract cron expression from config
    CRON_EXPRESSION=$(python3 -c "
import yaml
try:
    with open('/app/config/config.yml', 'r') as f:
        config = yaml.safe_load(f)
    print(config['scheduler']['cron'])
except Exception as e:
    print('0 8 1 * *')  # Default fallback
")

    # Create log directory
    mkdir -p /var/log

    # Create cron job
    echo "$CRON_EXPRESSION cd /app && python3 src/main.py >> /var/log/emby-newsletter.log 2>&1" | crontab -

    echo "Cron job scheduled: $CRON_EXPRESSION"
    echo "Logs will be written to: /var/log/emby-newsletter.log"
    echo "Starting cron daemon..."

    # Start cron in foreground
    cron -f
else
    echo "No scheduler configured. Running newsletter once..."
    cd /app && python3 src/main.py
fi