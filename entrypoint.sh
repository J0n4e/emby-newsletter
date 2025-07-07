#!/bin/bash

# Security: Set strict bash options
set -euo pipefail

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

# Read the scheduler configuration using safe Python script
SCHEDULER_ENABLED=$(python3 -c "
import yaml
import sys
import os
config_path = '/app/config/config.yml'
try:
    if not os.path.exists(config_path):
        print('false')
        sys.exit(0)
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    if not isinstance(config, dict):
        print('false')
        sys.exit(0)
    scheduler = config.get('scheduler', {})
    if isinstance(scheduler, dict) and 'cron' in scheduler and scheduler['cron']:
        print('true')
    else:
        print('false')
except Exception as e:
    print('false', file=sys.stderr)
    print(f'Error reading scheduler config: {e}', file=sys.stderr)
")

# If scheduler is enabled, set up cron job
if [ "$SCHEDULER_ENABLED" = "true" ]; then
    echo "Setting up scheduled newsletter..."

    # Extract cron expression from config using safe Python script
    CRON_EXPRESSION=$(python3 -c "
import yaml
import sys
import re
import os
config_path = '/app/config/config.yml'
try:
    if not os.path.exists(config_path):
        print('0 8 1 * *')  # Default fallback
        sys.exit(0)
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    if not isinstance(config, dict):
        print('0 8 1 * *')
        sys.exit(0)
    cron_expr = config.get('scheduler', {}).get('cron', '0 8 1 * *')
    # Basic validation of cron expression
    if isinstance(cron_expr, str) and re.match(r'^[0-9\*\-\,\/\s]+
, cron_expr.strip()):
        print(cron_expr.strip())
    else:
        print('0 8 1 * *')  # Default fallback
except Exception as e:
    print('0 8 1 * *', file=sys.stderr)  # Default fallback
    print(f'Error reading cron config: {e}', file=sys.stderr)
")

    # Create log directory
    mkdir -p /var/log

    # Validate cron expression format before using it
    if [[ "$CRON_EXPRESSION" =~ ^[0-9\*\-\,\/[:space:]]+$ ]]; then
        # Create cron job with safe command
        echo "$CRON_EXPRESSION cd /app && python3 src/main.py >> /var/log/emby-newsletter.log 2>&1" | crontab -

        echo "Cron job scheduled: $CRON_EXPRESSION"
        echo "Logs will be written to: /var/log/emby-newsletter.log"
        echo "Starting cron daemon..."

        # Start cron in foreground
        exec cron -f
    else
        echo "Error: Invalid cron expression format"
        exit 1
    fi
else
    echo "No scheduler configured. Running newsletter once..."
    cd /app && exec python3 src/main.py
fi