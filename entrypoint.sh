#!/bin/bash

# Security: Set strict bash options
set -euo pipefail

# Function to find Python executable
find_python() {
    # Try different possible Python executables
    for cmd in python python3 python3.11 /usr/local/bin/python /usr/local/bin/python3 /usr/bin/python /usr/bin/python3; do
        if command -v "$cmd" >/dev/null 2>&1; then
            echo "$cmd"
            return 0
        fi
    done

    # If nothing found, show debug info and exit
    echo "ERROR: No Python executable found!" >&2
    echo "Available executables in PATH:" >&2
    ls -la /usr/local/bin/python* 2>/dev/null || echo "No python in /usr/local/bin" >&2
    ls -la /usr/bin/python* 2>/dev/null || echo "No python in /usr/bin" >&2
    echo "PATH: $PATH" >&2
    exit 1
}

# Find Python executable
PYTHON_CMD=$(find_python)
echo "Using Python: $PYTHON_CMD ($($PYTHON_CMD --version))"

# Check if config file exists
if [ ! -f "/app/config/config.yml" ]; then
    echo "Error: Config file not found at /app/config/config.yml"
    echo "Please mount your config file to /app/config/config.yml"
    echo "Example: docker run -v ./config:/app/config ghcr.io/j0n4e/emby-newsletter"
    exit 1
fi

# Test configuration first
echo "Testing configuration..."
cd /app && $PYTHON_CMD check_config.py -c /app/config/config.yml --no-connectivity

if [ $? -ne 0 ]; then
    echo "Configuration validation failed. Please check your config file."
    exit 1
fi

# Read the scheduler configuration using safe Python script
SCHEDULER_ENABLED=$($PYTHON_CMD -c "
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
    CRON_EXPRESSION=$($PYTHON_CMD -c "
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
    if isinstance(cron_expr, str) and re.match(r'^[0-9\*\-\,\/\s]+$', cron_expr.strip()):
        print(cron_expr.strip())
    else:
        print('0 8 1 * *')  # Default fallback
except Exception as e:
    print('0 8 1 * *', file=sys.stderr)  # Default fallback
    print(f'Error reading cron config: {e}', file=sys.stderr)
")

    # Create necessary directories with proper permissions
    mkdir -p /var/log
    mkdir -p /var/spool/cron/crontabs
    chmod 0755 /var/spool/cron
    chmod 0755 /var/spool/cron/crontabs

    # Validate cron expression format before using it
    if [[ "$CRON_EXPRESSION" =~ ^[0-9\*\-\,\/[:space:]]+$ ]]; then
        # Create cron job with the detected Python command and proper environment
        echo "$CRON_EXPRESSION PATH=/usr/local/bin:/usr/bin:/bin PYTHONPATH=/app/source cd /app && $PYTHON_CMD source/main.py >> /var/log/emby-newsletter.log 2>&1" | crontab -

        echo "Cron job scheduled: $CRON_EXPRESSION"
        echo "Using Python command: $PYTHON_CMD"
        echo "Logs will be written to: /var/log/emby-newsletter.log"

        # Verify crontab was created
        echo "Verifying crontab installation..."
        if crontab -l > /dev/null 2>&1; then
            echo "✅ Crontab installed successfully:"
            crontab -l
        else
            echo "❌ Failed to install crontab"
            exit 1
        fi

        echo "Starting cron daemon..."

        # Start cron daemon in background
        cron

        # Verify cron is running
        if pgrep cron > /dev/null; then
            echo "✅ Cron daemon started successfully"
        else
            echo "❌ Failed to start cron daemon"
            exit 1
        fi

        # Keep container running by following the log files
        echo "Container running with cron scheduler..."
        echo "Following log files..."
        touch /var/log/emby-newsletter.log
        tail -f /var/log/emby-newsletter.log &

        # Keep the container alive
        while true; do
            sleep 60
            # Check if cron is still running
            if ! pgrep cron > /dev/null; then
                echo "❌ Cron daemon died, restarting..."
                cron
            fi
        done
    else
        echo "Error: Invalid cron expression format: $CRON_EXPRESSION"
        exit 1
    fi
else
    echo "No scheduler configured. Running newsletter once..."
    cd /app && exec $PYTHON_CMD source/main.py
fi