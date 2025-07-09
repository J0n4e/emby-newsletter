#!/bin/bash

# Security: Set strict bash options
set -euo pipefail

# =============================================================================
# TIMEZONE CONFIGURATION
# =============================================================================
echo "🔧 Setting up timezone configuration..."

# Check if TZ environment variable is set (from Docker)
if [ -n "${TZ:-}" ]; then
    echo "📍 TZ environment variable found: $TZ"

    # Validate timezone by checking if timezone file exists
    if [ -f "/usr/share/zoneinfo/$TZ" ]; then
        echo "🌍 Setting timezone to: $TZ"

        # Set system timezone
        ln -snf "/usr/share/zoneinfo/$TZ" /etc/localtime
        echo "$TZ" > /etc/timezone

        # Export TZ for all processes (including Python and cron)
        export TZ="$TZ"

        # Update timezone data if dpkg-reconfigure is available
        if command -v dpkg-reconfigure >/dev/null 2>&1; then
            echo "🔄 Updating timezone data..."
            DEBIAN_FRONTEND=noninteractive dpkg-reconfigure -f noninteractive tzdata 2>/dev/null || true
        fi

        echo "✅ Timezone configured successfully!"
        echo "   System time: $(date)"
        echo "   Timezone: $(date +%Z)"
        echo "   UTC offset: $(date +%z)"
    else
        echo "⚠️  Warning: Invalid timezone '$TZ' - timezone file not found"
        echo "   Available timezones: /usr/share/zoneinfo/"
        echo "   Falling back to UTC"
        export TZ="UTC"
    fi
else
    echo "⚠️  No TZ environment variable set"
    echo "   Set TZ environment variable in Docker (e.g., TZ=Europe/Bucharest)"
    echo "   Using UTC as fallback"
    export TZ="UTC"
fi

# =============================================================================
# CONFIGURATION VALIDATION
# =============================================================================

# Check if config file exists
if [ ! -f "/app/config/config.yml" ]; then
    echo "❌ Error: Config file not found at /app/config/config.yml"
    echo "Please mount your config file to /app/config/config.yml"
    echo "Example: docker run -v ./config:/app/config ghcr.io/j0n4e/emby-newsletter"
    exit 1
fi

# Test configuration first
echo "🔍 Testing configuration..."
cd /app && python3 check_config.py -c /app/config/config.yml --no-connectivity

if [ $? -ne 0 ]; then
    echo "❌ Configuration validation failed. Please check your config file."
    exit 1
fi

echo "✅ Configuration validation successful!"

# =============================================================================
# SCHEDULER CONFIGURATION
# =============================================================================

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
    echo "📅 Setting up scheduled newsletter..."

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

        # Create cron job with timezone environment properly set
        echo "🔧 Creating cron job with timezone: $TZ"

        # Create cron job that exports TZ before running Python
        echo "$CRON_EXPRESSION export TZ=\"$TZ\" && cd /app && /usr/local/bin/python3 source/main.py >> /var/log/emby-newsletter.log 2>&1" | crontab -

        echo "✅ Cron job scheduled successfully!"
        echo "   Expression: $CRON_EXPRESSION"
        echo "   Timezone: $TZ"
        echo "   Log file: /var/log/emby-newsletter.log"

        # Verify crontab was created
        echo ""
        echo "📋 Verifying crontab installation..."
        if crontab -l > /dev/null 2>&1; then
            echo "✅ Crontab installed successfully:"
            echo "--- Current Crontab ---"
            crontab -l
            echo "--- End Crontab ---"
        else
            echo "❌ Failed to install crontab"
            exit 1
        fi

        echo ""
        echo "🚀 Starting cron daemon..."

        # Start cron daemon with timezone environment
        cron

        # Verify cron is running
        sleep 1
        if pgrep cron > /dev/null; then
            echo "✅ Cron daemon started successfully (PID: $(pgrep cron))"
        else
            echo "❌ Failed to start cron daemon"
            exit 1
        fi

        # Display current time information for verification
        echo ""
        echo "=" * 60
        echo "🕐 TIMEZONE & SCHEDULE INFO"
        echo "=" * 60
        echo "Current system time: $(date)"
        echo "UTC time: $(date -u)"
        echo "Active timezone: $(date +%Z) (offset: $(date +%z))"
        echo "TZ environment: $TZ"
        echo "Cron schedule: $CRON_EXPRESSION"
        echo ""
        echo "📊 Next few executions (approximate):"
        echo "Monitor /var/log/emby-newsletter.log for actual execution times"
        echo "=" * 60
        echo ""

        # Keep container running by following the log files
        echo "🔄 Container running with scheduled newsletter..."
        echo "📝 Following newsletter logs..."
        echo ""

        # Create log file if it doesn't exist
        touch /var/log/emby-newsletter.log

        # Show any existing log content
        if [ -s /var/log/emby-newsletter.log ]; then
            echo "--- Recent Log Entries ---"
            tail -5 /var/log/emby-newsletter.log
            echo "--- End Recent Entries ---"
            echo ""
        fi

        # Follow the log file
        tail -f /var/log/emby-newsletter.log &
        TAIL_PID=$!

        # Keep the container alive and monitor cron
        while true; do
            sleep 60

            # Check if cron is still running
            if ! pgrep cron > /dev/null; then
                echo ""
                echo "❌ Cron daemon died, restarting..."
                cron
                sleep 2
                if pgrep cron > /dev/null; then
                    echo "✅ Cron daemon restarted successfully"
                else
                    echo "💥 Failed to restart cron daemon"
                    exit 1
                fi
            fi
        done
    else
        echo "❌ Error: Invalid cron expression format: $CRON_EXPRESSION"
        echo "Valid examples:"
        echo "  '0 8 * * *'     - Daily at 8 AM"
        echo "  '*/15 * * * *'  - Every 15 minutes"
        echo "  '0 8 1 * *'     - Monthly on 1st at 8 AM"
        exit 1
    fi
else
    echo "📧 No scheduler configured. Running newsletter once..."
    echo "💡 To enable scheduling, add 'cron: \"0 8 * * *\"' under 'scheduler' in config.yml"
    echo ""

    # Display current time info for one-time run
    echo "🕐 Running newsletter with timezone info:"
    echo "   System time: $(date)"
    echo "   Timezone: $(date +%Z)"
    echo "   TZ variable: $TZ"
    echo ""

    # Run newsletter once with timezone properly set
    cd /app && exec python3 source/main.py
fi