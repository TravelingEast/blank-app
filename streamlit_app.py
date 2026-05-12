"""
GlassCam AI — Streamlit dashboard

Shows the live POV feed from your repurposed Google Glass,
the AI conversation history, and a configuration panel.

Run (after starting server/app.py):
    streamlit run streamlit_app.py
"""

import time
from datetime import datetime

import requests
import streamlit as st

# ── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="GlassCam AI",
    page_icon="👓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar — configuration ─────────────────────────────────────────────────

with st.sidebar:
    st.title("👓 GlassCam AI")
    st.caption("Google Glass repurposed as an AI camera")

    st.subheader("Server")
    server_url = st.text_input(
        "Server URL",
        value="http://localhost:5000",
        help="Address of the companion server running server/app.py",
    )

    st.subheader("Capture settings")
    refresh_interval = st.slider(
        "Dashboard refresh (seconds)", min_value=1, max_value=30, value=3
    )
    history_limit = st.slider(
        "History to show", min_value=5, max_value=100, value=20
    )
    device_filter = st.text_input(
        "Filter by device ID", value="", placeholder="Leave blank for all devices"
    )

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear history", type="secondary", use_container_width=True):
            try:
                requests.delete(f"{server_url}/history", timeout=5)
                st.success("Cleared")
            except Exception as e:
                st.error(str(e))
    with col2:
        auto_refresh = st.toggle("Auto-refresh", value=True)

    st.divider()
    st.caption(
        "**Touchpad gestures on Glass**\n\n"
        "- Single tap → capture now\n"
        "- Swipe back → pause / resume\n\n"
        "**ADB commands**\n\n"
        "```\n"
        "# Capture now\n"
        "adb shell am startservice \\\n"
        "  -n com.glasscam/.CameraStreamService \\\n"
        "  -a com.glasscam.CAPTURE_NOW\n\n"
        "# Toggle pause\n"
        "adb shell am startservice \\\n"
        "  -n com.glasscam/.CameraStreamService \\\n"
        "  -a com.glasscam.TOGGLE_PAUSE\n"
        "```"
    )

# ── Health check ─────────────────────────────────────────────────────────────

def check_server(url: str) -> bool:
    try:
        r = requests.get(f"{url}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


server_ok = check_server(server_url)
status_badge = "🟢 Server connected" if server_ok else "🔴 Server offline"
st.markdown(f"**{status_badge}**  •  `{server_url}`")

if not server_ok:
    st.warning(
        "Cannot reach the server. Make sure `server/app.py` is running:\n\n"
        "```bash\ncd server && uvicorn app:app --host 0.0.0.0 --port 5000\n```"
    )
    st.stop()

# ── Main layout ───────────────────────────────────────────────────────────────

col_feed, col_chat = st.columns([1, 1], gap="large")

# ── Live feed ────────────────────────────────────────────────────────────────

with col_feed:
    st.subheader("Live POV")
    frame_placeholder = st.empty()
    meta_placeholder = st.empty()

    params = {"device_id": device_filter} if device_filter else {}

    try:
        frame_resp = requests.get(
            f"{server_url}/latest_frame", params=params, timeout=5
        )
        if frame_resp.status_code == 200:
            frame_placeholder.image(
                frame_resp.content,
                caption="Latest frame from Glass",
                use_container_width=True,
            )
        else:
            frame_placeholder.info("No frames received yet. Put on your Glass and wait for the first capture.")
    except Exception as exc:
        frame_placeholder.error(f"Frame fetch error: {exc}")

# ── AI conversation history ───────────────────────────────────────────────────

with col_chat:
    st.subheader("AI Responses")

    try:
        hist_resp = requests.get(
            f"{server_url}/history",
            params={"limit": history_limit, **({"device_id": device_filter} if device_filter else {})},
            timeout=5,
        )
        rows = hist_resp.json() if hist_resp.status_code == 200 else []
    except Exception:
        rows = []

    if not rows:
        st.info("No conversation history yet.")
    else:
        for row in rows:
            ts = row.get("ts", "")
            try:
                ts_fmt = datetime.fromisoformat(ts).strftime("%H:%M:%S")
            except Exception:
                ts_fmt = ts

            device = row.get("device_id", "?")
            prompt = row.get("prompt", "")
            response = row.get("response", "")
            latency = row.get("latency_ms", 0)
            model = row.get("model", "")

            with st.container(border=True):
                header_col, meta_col = st.columns([3, 1])
                with header_col:
                    st.markdown(f"**{ts_fmt}** · `{device}`")
                with meta_col:
                    st.caption(f"{latency} ms · {model.split('-')[1] if '-' in model else model}")

                if prompt != "Briefly describe what you see in one sentence.":
                    st.markdown(f"*Prompt:* {prompt}")

                st.markdown(f"> {response}")

# ── Stats bar ────────────────────────────────────────────────────────────────

if rows:
    st.divider()
    total = len(rows)
    avg_latency = sum(r.get("latency_ms", 0) for r in rows) / max(total, 1)
    devices = len({r.get("device_id") for r in rows})

    m1, m2, m3 = st.columns(3)
    m1.metric("Captures shown", total)
    m2.metric("Avg AI latency", f"{avg_latency:.0f} ms")
    m3.metric("Devices", devices)

# ── Auto-refresh ──────────────────────────────────────────────────────────────

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
