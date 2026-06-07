#!/bin/bash
# Gateway watchdog - silent mode: only outputs on failure
GATEWAY_PID=$(pgrep -f 'hermes_cli.main gateway' 2>/dev/null || true)
if [ -z "$GATEWAY_PID" ]; then
    echo "⚠️ Hermes Gateway is DOWN at $(date)"
    echo "Attempting restart..."
    systemctl --user restart hermes-gateway 2>&1
    sleep 3
    if pgrep -f 'hermes_cli.main gateway' >/dev/null 2>&1; then
        echo "✅ Gateway restarted successfully"
    else
        echo "❌ FAILED: Gateway still down after restart attempt"
    fi
fi
# Gateway is running? Silent exit — no news is good news.
