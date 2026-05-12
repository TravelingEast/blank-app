#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# GlassCam AI — sideload helper
#
# Prerequisites on your Glass (do once):
#   1. Settings → Privacy → Developer options → Enable
#   2. Connect via USB
#   3. On the first run, accept the RSA key fingerprint on the touchpad
#
# Usage:
#   ./sideload.sh              # install APK + push config
#   ./sideload.sh --config     # push updated config only
#   ./sideload.sh --start      # start service via ADB (no reinstall)
#   ./sideload.sh --stop       # stop service
#   ./sideload.sh --logs       # stream logcat filtered to GlassCam
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

APK="glass_app/glasscam-debug.apk"          # built by Android Studio / gradlew
CONF="glass_app/glasscam.conf"
REMOTE_CONF="/sdcard/glasscam/glasscam.conf"
PACKAGE="com.glasscam"
SERVICE="$PACKAGE/.CameraStreamService"
MAIN_ACTIVITY="$PACKAGE/.MainActivity"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

ok()   { echo -e "${GREEN}✓${NC}  $*"; }
warn() { echo -e "${YELLOW}⚠${NC}  $*"; }
err()  { echo -e "${RED}✗${NC}  $*"; exit 1; }

check_adb() {
    command -v adb >/dev/null 2>&1 || err "adb not found — install Android platform-tools"
    adb devices | grep -q "device$" || err "No Glass detected. Enable ADB and connect via USB."
    ok "Glass detected"
}

push_config() {
    adb shell mkdir -p /sdcard/glasscam
    adb push "$CONF" "$REMOTE_CONF"
    ok "Config pushed to $REMOTE_CONF"
    warn "Edit $CONF to set your server IP before pushing"
}

install_apk() {
    [ -f "$APK" ] || err "APK not found at $APK — build with: cd glass_app && ./gradlew assembleDebug"
    adb install -r "$APK"
    ok "APK installed"
}

start_service() {
    # Launch the main activity (which starts the service)
    adb shell am start -n "$MAIN_ACTIVITY"
    ok "GlassCam started"
}

stop_service() {
    adb shell am stopservice -n "$SERVICE" || true
    ok "GlassCam stopped"
}

stream_logs() {
    warn "Streaming GlassCam logs (Ctrl-C to stop)…"
    adb logcat -c
    adb logcat -s "GlassCam/Service:D" "GlassCam/Config:D" "GlassCam/Boot:D"
}

# ── Dispatch ──────────────────────────────────────────────────────────────────

case "${1:-install}" in
    install|"")
        check_adb
        install_apk
        push_config
        start_service
        ;;
    --config|-c)
        check_adb
        push_config
        ;;
    --start|-s)
        check_adb
        start_service
        ;;
    --stop)
        check_adb
        stop_service
        ;;
    --logs|-l)
        check_adb
        stream_logs
        ;;
    --capture)
        check_adb
        adb shell am startservice -n "$SERVICE" -a com.glasscam.CAPTURE_NOW
        ok "Manual capture triggered"
        ;;
    --pause)
        check_adb
        adb shell am startservice -n "$SERVICE" -a com.glasscam.TOGGLE_PAUSE
        ok "Pause toggled"
        ;;
    *)
        echo "Usage: $0 [install|--config|--start|--stop|--logs|--capture|--pause]"
        exit 1
        ;;
esac
