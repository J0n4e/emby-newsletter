#!/bin/bash

# Security: Set strict bash options
set -euo pipefail

# =============================================================================
# CONFIGURATION CHECK
# =============================================================================

# Check if config file exists
if [ ! -f "/app/config/config.yml" ]; then
    echo "Error: Config file not found at /app/config/config.yml"
    echo "Please mount your config file to /app/config/config.yml"
    echo "Example: docker run -v ./config:/app/config ghcr.io/j0n4e/emby-newsletter"
    exit 1
fi

# =============================================================================
# TIMEZONE CONFIGURATION FROM CONFIG FILE
# =============================================================================

# Extract timezone from config file, with fallback to TZ environment variable
CONFIG_TIMEZONE=$(python3 -c "
import yaml
import sys
import os
config_path = '/app/config/config.yml'
try:
    if not os.path.exists(config_path):
        print('${TZ:-UTC}')
        sys.exit(0)
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    if not isinstance(config, dict):
        print('${TZ:-UTC}')
        sys.exit(0)

    # Try to get timezone from scheduler config first
    scheduler_tz = config.get('scheduler', {}).get('timezone', '')
    if scheduler_tz and isinstance(scheduler_tz, str):
        print(scheduler_tz.strip())
    else:
        # Fallback to environment variable or UTC
        print('${TZ:-UTC}')
except Exception as e:
    print('${TZ:-UTC}', file=sys.stderr)
    print(f'Error reading timezone from config: {e}', file=sys.stderr)
" 2>/dev/null)

# Set the timezone
if [ -n "$CONFIG_TIMEZONE" ] && [ "$CONFIG_TIMEZONE" != "UTC" ]; then
    echo "🌍 Setting timezone from config: $CONFIG_TIMEZONE"

    # Check if timezone file exists
    if [ -f "/usr/share/zoneinfo/$CONFIG_TIMEZONE" ]; then
        # Set system timezone
        ln -snf "/usr/share/zoneinfo/$CONFIG_TIMEZONE" /etc/localtime
        echo "$CONFIG_TIMEZONE" > /etc/timezone

        # Export TZ for all processes
        export TZ="$CONFIG_TIMEZONE"

        # Update tzdata cache if available
        if command -v dpkg-reconfigure >/dev/null 2>&1; then
            AREA=$(echo $CONFIG_TIMEZONE | cut -d'/' -f1)
            ZONE=$(echo $CONFIG_TIMEZONE | cut -d'/' -f2-)
            echo "tzdata tzdata/Areas select $AREA" | debconf-set-selections 2>/dev/null || true
            echo "tzdata tzdata/Zones/$AREA select $ZONE" | debconf-set-selections 2>/dev/null || true
            dpkg-reconfigure -f noninteractive tzdata 2>/dev/null || true
        fi

        # Verify timezone is set correctly
        echo "✅ Timezone configured successfully:"
        echo "   Config timezone: $CONFIG_TIMEZONE"
        echo "   System time: $(date)"
        echo "   Timezone: $(date +%Z)"
        echo "   UTC offset: $(date +%z)"
    else
        echo "⚠️  Warning: Timezone file not found for $CONFIG_TIMEZONE"
        echo "   Available timezones: /usr/share/zoneinfo/"
        echo "   Falling back to UTC"
        export TZ="UTC"
    fi
elif [ -n "${TZ:-}" ]; then
    echo "🌍 Using TZ environment variable: $TZ"
    if [ -f "/usr/share/zoneinfo/$TZ" ]; then
        ln -snf "/usr/share/zoneinfo/$TZ" /etc/localtime
        echo "$TZ" > /etc/timezone
        export TZ="$TZ"
        echo "✅ Environment timezone set: $(date)"
    else
        echo "⚠️  Invalid TZ environment variable: $TZ"
        export TZ="UTC"
    fi
else
    echo "⚠️  No timezone configured in config.yml or TZ environment variable"
    echo "   Add 'timezone: Europe/Bucharest' under the scheduler section in config.yml"
    echo "   Using UTC as fallback"
    export TZ="UTC"
fi

# =============================================================================
# CONFIGURATION VALIDATION
# =============================================================================

# Test configuration first
echo "Testing configuration..."
cd /app && python3 check_config.py -c /app/config/config.yml --no-connectivity

if [ $? -ne 0 ]; then
    echo "Configuration validation failed. Please check your config file."
    exit 1
fi

# =============================================================================
# SCHEDULER CONFIGURATION
# =============================================================================

# Read the scheduler configuration using safe Python script
SCHEDULER_CONFIG=$(python3 -c "
import yaml
import sys
import os
import json
config_path = '/app/config/config.yml'
try:
    if not os.path.exists(config_path):
        print(json.dumps({'enabled': False, 'cron': '0 8 1 * *', 'timezone': 'UTC'}))
        sys.exit(0)
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    if not isinstance(config, dict):
        print(json.dumps({'enabled': False, 'cron': '0 8 1 * *', 'timezone': 'UTC'}))
        sys.exit(0)

    scheduler = config.get('scheduler', {})
    result = {
        'enabled': isinstance(scheduler, dict) and 'cron' in scheduler and bool(scheduler['cron']),
        'cron': scheduler.get('cron', '0 8 1 * *') if isinstance(scheduler, dict) else '0 8 1 * *',
        'timezone': scheduler.get('timezone', 'UTC') if isinstance(scheduler, dict) else 'UTC'
    }
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({'enabled': False, 'cron': '0 8 1 * *', 'timezone': 'UTC'}), file=sys.stderr)
    print(f'Error reading scheduler config: {e}', file=sys.stderr)
")

# Parse the JSON response
SCHEDULER_ENABLED=$(echo "$SCHEDULER_CONFIG" | python3 -c "import json, sys; data=json.load(sys.stdin); print('true' if data['enabled'] else 'false')")
CRON_EXPRESSION=$(echo "$SCHEDULER_CONFIG" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data['cron'])")
CRON_TIMEZONE=$(echo "$SCHEDULER_CONFIG" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data['timezone'])")

# If scheduler is enabled, set up cron job
if [ "$SCHEDULER_ENABLED" = "true" ]; then
    echo "Setting up scheduled newsletter..."
    echo "📅 Schedule: $CRON_EXPRESSION"
    echo "🌍 Timezone: ${TZ:-UTC}"

    # Create necessary directories with proper permissions
    mkdir -p /var/log
    mkdir -p /var/spool/cron/crontabs
    chmod 0755 /var/spool/cron
    chmod 0755 /var/spool/cron/crontabs

    # Validate cron expression format before using it
    if echo "$CRON_EXPRESSION" | grep -qE '^[0-9\*\-\,\/[:space:]]+$'; then

        # Create cron environment file with timezone
        cat > /tmp/cron_env << CRONEOF
TZ=${TZ:-UTC}
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
LANG=C.UTF-8
CRONEOF

        # Create cron job with timezone environment
        (
            echo "# Emby Newsletter Cron Environment"
            cat /tmp/cron_env
            echo ""
            echo "# Emby Newsletter scheduled job"
            echo "# Runs: $CRON_EXPRESSION"
            echo "# Timezone: ${TZ:-UTC}"
            echo "$CRON_EXPRESSION cd /app && TZ=\"${TZ:-UTC}\" /usr/local/bin/python3 source/main.py >> /var/log/emby-newsletter.log 2>&1"
        ) | crontab -

        echo "✅ Cron job scheduled successfully"
        echo "📋 Schedule details:"
        echo "   Expression: $CRON_EXPRESSION"
        echo "   Timezone: ${TZ:-UTC}"
        echo "   Log file: /var/log/emby-newsletter.log"

        # Verify crontab was created
        echo ""
        echo "📝 Verifying crontab installation..."
        if crontab -l > /dev/null 2>&1; then
            echo "✅ Crontab installed successfully:"
            echo "--- Crontab Content ---"
            crontab -l | grep -v "^#" | grep -v "^$" || echo "   (Only environment and job lines shown)"
            echo "--- End Crontab ---"
        else
            echo "❌ Failed to install crontab"
            exit 1
        fi

        echo ""
        echo "🚀 Starting cron daemon..."

        # Start cron daemon in background with timezone
        cron

        # Verify cron is running
        sleep 1
        if pgrep cron > /dev/null; then
            echo "✅ Cron daemon started successfully (PID: $(pgrep cron))"
        else
            echo "❌ Failed to start cron daemon"
            exit 1
        fi

        # Display comprehensive time information
        echo ""
        echo "=" * 60
        echo "📅 TIMEZONE & SCHEDULE SUMMARY"
        echo "=" * 60
        echo "   Current time: $(date)"
        echo "   UTC time: $(date -u)"
        echo "   Timezone: $(date +%Z) ($(date +%z))"
        echo "   Config timezone: ${CRON_TIMEZONE:-Not set}"
        echo "   Active timezone: ${TZ:-UTC}"
        echo "   Cron schedule: $CRON_EXPRESSION"
        echo ""
        echo "   Next estimated runs:"

        # Show next few execution times using a simple estimation
        python3 -c "
import datetime
import os
tz_name = os.environ.get('TZ', 'UTC')
cron = '$CRON_EXPRESSION'
print(f'   • Cron will execute: {cron}')
print(f'   • Monitor logs at: /var/log/emby-newsletter.log')
print(f'   • Timezone: {tz_name}')
"
        echo "=" * 60
        echo ""

        # Keep container running by following the log files
        echo "🔄 Container running with cron scheduler..."
        echo "📊 Following newsletter logs (Ctrl+C to stop log viewing)..."
        echo ""
        touch /var/log/emby-newsletter.log

        # Show last few lines of log if any exist
        if [ -s /var/log/emby-newsletter.log ]; then
            echo "--- Recent log entries ---"
            tail -5 /var/log/emby-newsletter.log
            echo "--- End recent entries ---"
            echo ""
        fi

        tail -f /var/log/emby-newsletter.log &
        TAIL_PID=$!

        # Keep the container alive and monitor cron
        while true; do
            sleep 60
            # Check if cron is still running
            if ! pgrep cron > /dev/null; then
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
        echo "   Example valid formats:"
        echo "   • '0 8 * * *'     (daily at 8 AM)"
        echo "   • '*/15 * * * *'  (every 15 minutes)"
        echo "   • '0 8 1 * *'     (monthly on 1st at 8 AM)"
        exit 1
    fi
else
    echo "📧 No scheduler configured. Running newsletter once..."
    echo "💡 To enable scheduling, add a 'cron' field under 'scheduler' in config.yml"
    echo ""

    # Show current timezone info for one-time run
    echo "🕐 Current time info:"
    echo "   Time: $(date)"
    echo "   Timezone: $(date +%Z)"
    echo "   Using timezone: ${TZ:-UTC}"
    echo ""

    # Run newsletter once
    cd /app && exec python3 source/main.py
fi