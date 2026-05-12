#!/usr/bin/env bash
# Start the GlassCam AI server.
# Run this on the machine (laptop, desktop, or phone-hotspot-connected device)
# that Glass will talk to over WiFi.
set -euo pipefail

cd "$(dirname "$0")"

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    echo "Error: ANTHROPIC_API_KEY is not set."
    echo "  export ANTHROPIC_API_KEY=sk-ant-..."
    exit 1
fi

pip install -q -r requirements.txt

echo "Starting GlassCam AI server on port 5000…"
echo "Your local IPs:"
hostname -I 2>/dev/null || ifconfig | grep 'inet ' | awk '{print $2}' || true
echo ""
echo "Put the correct IP in glass_app/glasscam.conf, then run:  ./sideload.sh --config"
echo ""

uvicorn app:app --host 0.0.0.0 --port 5000 --reload
