# GlassCam AI

Repurpose a pair of **Google Glass** (Explorer Edition XE or Enterprise Edition 2) as an always-on AI camera. No display needed — audio feedback through the bone conduction speaker is the only output.

```
Glass camera  →  WiFi  →  AI server  →  Claude vision  →  spoken response
                               ↓
                       Streamlit dashboard (live feed + history)
```

---

## What it does

| Component | Description |
|-----------|-------------|
| **Glass app** (`glass_app/`) | Android app that captures 720p frames at a configurable interval, POSTs them to the server, and speaks Claude's one-sentence response through the bone conduction speaker. Auto-starts on boot. |
| **AI server** (`server/`) | FastAPI server that receives frames, calls the Claude vision API, stores results in SQLite, and serves them to the dashboard. |
| **Dashboard** (`streamlit_app.py`) | Live POV feed, scrollable AI conversation history, latency stats. |

---

## Hardware

- **Google Glass Explorer Edition** (XE10–XE22) — Android 4.4, Camera API 1
- **Google Glass Enterprise Edition 2** — Android 8.1, also supported
- The display module can be physically removed; the app does not need it
- Glass must be on the same WiFi network as the server (or the server can run on a phone hotspot that Glass connects to)

---

## Quick start

### 1 — Build the Android APK

```bash
# Requires Android Studio or the Android command-line tools
cd glass_app
./gradlew assembleDebug
# APK: glass_app/app/build/outputs/apk/debug/app-debug.apk
cp app/build/outputs/apk/debug/app-debug.apk glasscam-debug.apk
```

### 2 — Configure

Edit `glass_app/glasscam.conf`:

```ini
server_url=http://192.168.1.100:5000   # your server's LAN IP
interval=4                              # seconds between captures
prompt=Briefly describe what you see in one sentence.
```

### 3 — Start the AI server

```bash
export ANTHROPIC_API_KEY=sk-ant-...
./server/start_server.sh
```

### 4 — Sideload onto Glass

Enable **Developer Options** on Glass: *Settings → Privacy → Developer options → Enable*.
Connect via USB, accept the RSA key prompt on the touchpad, then:

```bash
./sideload.sh          # installs APK, pushes config, starts app
```

Subsequent config changes only:
```bash
./sideload.sh --config
```

### 5 — Open the dashboard

```bash
streamlit run streamlit_app.py
```

---

## Glass touchpad controls

| Gesture | Action |
|---------|--------|
| Single tap | Capture frame immediately |
| Swipe back (forward to back) | Pause / resume auto-capture |

---

## ADB commands (no touchpad needed)

```bash
./sideload.sh --capture    # trigger a capture now
./sideload.sh --pause      # toggle pause
./sideload.sh --logs       # stream filtered logcat
./sideload.sh --stop       # stop the service
```

---

## Removing the display

The Glass display module (the prism + projector assembly) slots into the main frame.
On XE hardware it can be removed by sliding it off the titanium band — the app runs
entirely as a background service and does not need it. The camera, WiFi, bone
conduction speaker, touchpad, and microphone are all on the main frame.

---

## Configuration reference (`glasscam.conf`)

| Key | Default | Description |
|-----|---------|-------------|
| `server_url` | `http://192.168.1.100:5000` | AI server address |
| `interval` | `4` | Seconds between automatic captures (min 2) |
| `prompt` | *"Briefly describe…"* | Default prompt sent with each frame |
| `device_id` | device serial | Name shown in dashboard |
| `save_locally` | `true` | Also save JPEGs to `/sdcard/glasscam/captures/` |
| `stream` | `true` | Send frames to server |
| `jpeg_quality` | `80` | JPEG compression (0–100) |

Push an updated config without reinstalling:
```bash
adb push glass_app/glasscam.conf /sdcard/glasscam/glasscam.conf
```

---

## Server API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/upload_frame` | POST | Receive JPEG, return AI text |
| `/history` | GET | Recent captures (JSON) |
| `/latest_frame` | GET | Most recent JPEG |
| `/history` | DELETE | Clear all captures |

---

## Architecture notes

- **No GDK dependency** — uses standard Android `Camera` (API 1) and `TextToSpeech`, so it works on both XE and Enterprise Glass without the Glass Development Kit.
- **Zero third-party Android libraries** — the APK depends only on the Android framework, keeping it small and compatible with older firmware.
- **Fallback storage** — if the server is unreachable, frames are saved locally to the SD card and can be retrieved later with `adb pull /sdcard/glasscam/captures/`.
- **Audio-first design** — all AI responses are constrained to one sentence to work well as spoken audio.
