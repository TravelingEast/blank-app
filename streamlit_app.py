import streamlit as st
import socket
import base64
import json
from typing import Optional, Dict, List
import time

st.set_page_config(page_title="Samsung TV Controller", layout="wide")

st.title("📺 Samsung TV Controller")
st.markdown("Control your Samsung TV's volume and input from your browser")

class SamsungTVController:
    def __init__(self, ip: str, port: int = 8002):
        self.ip = ip
        self.port = port
        self.sock = None

    def _send_raw_command(self, command: str) -> bool:
        try:
            if self.sock is None:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(3)
                self.sock.connect((self.ip, self.port))

            self.sock.sendall(command.encode())
            time.sleep(0.1)
            return True
        except Exception as e:
            self.sock = None
            st.error(f"Connection failed: {str(e)}")
            return False

    def volume_up(self) -> bool:
        return self._send_key("KEY_VOL_UP")

    def volume_down(self) -> bool:
        return self._send_key("KEY_VOL_DOWN")

    def _send_key(self, key: str) -> bool:
        try:
            payload = {
                "method": "ms.remote.control",
                "params": {
                    "Cmd": "Click",
                    "DataOfCmd": key,
                    "TypeOfRemote": "SendRemoteKey"
                }
            }
            msg = json.dumps(payload)
            return self._send_raw_command(msg)
        except Exception as e:
            st.error(f"Failed to send key: {str(e)}")
            return False

    def is_alive(self) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((self.ip, self.port))
            sock.close()
            return result == 0
        except:
            return False

def discover_samsung_tvs() -> List[str]:
    """Attempt to discover Samsung TVs on local network"""
    discovered = []
    local_ip = socket.gethostbyname(socket.gethostname())
    subnet = ".".join(local_ip.split(".")[:-1])

    st.info("🔍 Scanning for Samsung TVs... (this may take a moment)")

    for i in range(1, 50):
        ip = f"{subnet}.{i}"
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((ip, 8002))
            if result == 0:
                controller = SamsungTVController(ip)
                if controller.is_alive():
                    discovered.append(ip)
            sock.close()
        except:
            pass

    return discovered

# Sidebar for TV connection
with st.sidebar:
    st.header("📱 Connection Settings")

    connection_method = st.radio("Connect to TV:", ["Manual IP", "Auto Discover"])
    tv_ip = ""

    if connection_method == "Manual IP":
        tv_ip = st.text_input("TV IP Address", "192.168.1.", placeholder="e.g., 192.168.1.100")
    else:
        if st.button("🔍 Discover TVs"):
            with st.spinner("Scanning network..."):
                discovered = discover_samsung_tvs()
            if discovered:
                st.success(f"Found {len(discovered)} TV(s)")
                tv_ip = st.selectbox("Select TV:", discovered)
            else:
                st.warning("No TVs found. Try manual connection.")
                tv_ip = st.text_input("TV IP Address", placeholder="e.g., 192.168.1.100")
        else:
            tv_ip = st.text_input("TV IP Address", placeholder="e.g., 192.168.1.100")

    if tv_ip and st.button("🔗 Connect", key="connect_btn"):
        st.session_state.tv_ip = tv_ip
        st.session_state.controller = SamsungTVController(tv_ip)
        st.success(f"Connected to {tv_ip}")

# Main controls
if "controller" not in st.session_state:
    st.info("👉 Enter your TV's IP address in the sidebar and connect")
else:
    controller = st.session_state.controller

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔊 Volume Control")
        vol_col1, vol_col2, vol_col3 = st.columns(3)

        with vol_col1:
            if st.button("➖ Volume Down", key="vol_down"):
                if controller.volume_down():
                    st.success("Volume decreased")
                else:
                    st.error("Failed to change volume")

        with vol_col2:
            st.write("")  # spacer

        with vol_col3:
            if st.button("➕ Volume Up", key="vol_up"):
                if controller.volume_up():
                    st.success("Volume increased")
                else:
                    st.error("Failed to change volume")

    with col2:
        st.subheader("📺 Input/Source Control")
        input_col1, input_col2, input_col3 = st.columns(3)

        with input_col1:
            if st.button("📺 HDMI 1", key="hdmi1"):
                if controller._send_key("KEY_HDMI"):
                    st.success("Switched to HDMI")
                else:
                    st.error("Failed to switch input")

        with input_col2:
            if st.button("📺 HDMI 2", key="hdmi2"):
                if controller._send_key("KEY_HDMI1"):
                    st.success("Switched to HDMI 2")
                else:
                    st.error("Failed to switch input")

        with input_col3:
            if st.button("📺 TV/Cable", key="tvcable"):
                if controller._send_key("KEY_TV"):
                    st.success("Switched to TV")
                else:
                    st.error("Failed to switch input")

    st.divider()

    # Quick actions
    st.subheader("⚡ Quick Commands")
    quick_col1, quick_col2, quick_col3 = st.columns(3)

    with quick_col1:
        if st.button("🔴 Power Off", key="power_off"):
            if controller._send_key("KEY_POWER"):
                st.success("Power command sent")
            else:
                st.error("Failed to send power command")

    with quick_col2:
        if st.button("🔇 Mute", key="mute"):
            if controller._send_key("KEY_MUTE"):
                st.success("Mute toggled")
            else:
                st.error("Failed to mute")

    with quick_col3:
        if st.button("🏠 Home", key="home"):
            if controller._send_key("KEY_HOME"):
                st.success("Home pressed")
            else:
                st.error("Failed to go home")
