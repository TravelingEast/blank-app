import streamlit as st
import socket
import requests
import json
from typing import Optional, Dict, List
import time

st.set_page_config(page_title="TV Remote Controller", layout="wide")

st.title("📺 Smart TV Remote Controller")
st.markdown("Control your Samsung or LG TV's volume and input from your browser")

class TVController:
    def __init__(self, ip: str, brand: str = "Samsung"):
        self.ip = ip
        self.brand = brand.lower()
        self.sock = None

    def test_connection(self) -> Dict:
        results = {
            "port_8002": False,
            "port_8008": False,
            "port_3000": False,
            "port_9000": False
        }

        ports = [8002, 8008, 3000, 9000]
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((self.ip, port))
                sock.close()
                results[f"port_{port}"] = (result == 0)
            except:
                pass

        return results

    def send_samsung_command(self, key: str) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((self.ip, 8002))

            payload = {
                "method": "ms.remote.control",
                "params": {
                    "Cmd": "Click",
                    "DataOfCmd": key,
                    "TypeOfRemote": "SendRemoteKey"
                }
            }

            msg = json.dumps(payload) + "\n"
            sock.sendall(msg.encode())
            sock.close()
            return True
        except Exception as e:
            st.error(f"Samsung command failed: {str(e)}")
            return False

    def send_lg_command(self, button: str) -> bool:
        try:
            # LG uses port 8008 with HTTP API
            url = f"http://{self.ip}:8008/roap/api/command"

            payload = {
                "type": "execute",
                "value": button
            }

            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=payload, headers=headers, timeout=2)
            return response.status_code in [200, 201]
        except Exception as e:
            st.error(f"LG command failed: {str(e)}")
            return False

    def volume_up(self) -> bool:
        if self.brand == "samsung":
            return self.send_samsung_command("KEY_VOL_UP")
        else:
            return self.send_lg_command("VOLUMEUP")

    def volume_down(self) -> bool:
        if self.brand == "samsung":
            return self.send_samsung_command("KEY_VOL_DOWN")
        else:
            return self.send_lg_command("VOLUMEDOWN")

    def mute(self) -> bool:
        if self.brand == "samsung":
            return self.send_samsung_command("KEY_MUTE")
        else:
            return self.send_lg_command("MUTE")

    def power(self) -> bool:
        if self.brand == "samsung":
            return self.send_samsung_command("KEY_POWER")
        else:
            return self.send_lg_command("POWER")

    def home(self) -> bool:
        if self.brand == "samsung":
            return self.send_samsung_command("KEY_HOME")
        else:
            return self.send_lg_command("HOME")

    def channel_up(self) -> bool:
        if self.brand == "samsung":
            return self.send_samsung_command("KEY_CH_UP")
        else:
            return self.send_lg_command("CHANNELUP")

    def channel_down(self) -> bool:
        if self.brand == "samsung":
            return self.send_samsung_command("KEY_CH_DOWN")
        else:
            return self.send_lg_command("CHANNELDOWN")

    def input_hdmi(self, num: int = 1) -> bool:
        if self.brand == "samsung":
            key = f"KEY_HDMI{num if num > 1 else ''}"
            return self.send_samsung_command(key)
        else:
            return self.send_lg_command(f"HDMI{num}")


# Sidebar for TV connection
with st.sidebar:
    st.header("📱 Connection Settings")

    tv_brand = st.radio("TV Brand:", ["Samsung", "LG"])

    connection_method = st.radio("Connect to TV:", ["Manual IP", "Auto Discover"])
    tv_ip = ""

    if connection_method == "Manual IP":
        tv_ip = st.text_input("TV IP Address", "192.168.", placeholder="e.g., 192.168.1.100")
    else:
        if st.button("🔍 Discover TVs"):
            with st.spinner("Scanning network..."):
                discovered = []
                local_ip = socket.gethostbyname(socket.gethostname())
                subnet = ".".join(local_ip.split(".")[:-1])

                for i in range(1, 100):
                    ip = f"{subnet}.{i}"
                    for port in [8002, 8008, 3000, 9000]:
                        try:
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(0.3)
                            if sock.connect_ex((ip, port)) == 0:
                                if ip not in discovered:
                                    discovered.append(ip)
                            sock.close()
                        except:
                            pass

            if discovered:
                st.success(f"Found {len(discovered)} device(s)")
                tv_ip = st.selectbox("Select TV:", discovered)
            else:
                st.warning("No TVs found. Try manual connection.")
                tv_ip = st.text_input("TV IP Address", placeholder="e.g., 192.168.1.100")
        else:
            tv_ip = st.text_input("TV IP Address", placeholder="e.g., 192.168.1.100")

    if tv_ip and st.button("🔗 Connect", key="connect_btn"):
        st.session_state.tv_ip = tv_ip
        st.session_state.tv_brand = tv_brand
        st.session_state.controller = TVController(tv_ip, tv_brand)
        st.success(f"Connected to {tv_brand} TV at {tv_ip}")

# Main controls
if "controller" not in st.session_state:
    st.info("👉 Enter your TV's IP address in the sidebar and connect")
else:
    controller = st.session_state.controller
    tv_brand = st.session_state.tv_brand

    # Connection diagnostics
    with st.expander("🔧 Connection Diagnostics"):
        if st.button("Test Ports"):
            results = controller.test_connection()
            for port, status in results.items():
                emoji = "✓" if status else "✗"
                st.write(f"{emoji} {port}: {status}")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔊 Volume Control")
        vol_col1, vol_col2, vol_col3 = st.columns(3)

        with vol_col1:
            if st.button("➖ Volume Down", key="vol_down", use_container_width=True):
                if controller.volume_down():
                    st.success("Volume decreased")

        with vol_col2:
            st.write("")  # spacer

        with vol_col3:
            if st.button("➕ Volume Up", key="vol_up", use_container_width=True):
                if controller.volume_up():
                    st.success("Volume increased")

    with col2:
        st.subheader("📺 Channel Control")
        ch_col1, ch_col2, ch_col3 = st.columns(3)

        with ch_col1:
            if st.button("⬅️ Channel Down", key="ch_down", use_container_width=True):
                if controller.channel_down():
                    st.success("Channel decreased")

        with ch_col2:
            st.write("")

        with ch_col3:
            if st.button("➡️ Channel Up", key="ch_up", use_container_width=True):
                if controller.channel_up():
                    st.success("Channel increased")

    st.divider()

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("📡 Input/Source")
        input_col1, input_col2 = st.columns(2)

        with input_col1:
            if st.button("📺 HDMI 1", key="hdmi1", use_container_width=True):
                if controller.input_hdmi(1):
                    st.success("Switched to HDMI 1")

        with input_col2:
            if st.button("📺 HDMI 2", key="hdmi2", use_container_width=True):
                if controller.input_hdmi(2):
                    st.success("Switched to HDMI 2")

    with col4:
        st.subheader("⚡ Quick Commands")
        quick_col1, quick_col2 = st.columns(2)

        with quick_col1:
            if st.button("🔴 Power", key="power", use_container_width=True):
                if controller.power():
                    st.success("Power command sent")

        with quick_col2:
            if st.button("🔇 Mute", key="mute", use_container_width=True):
                if controller.mute():
                    st.success("Mute toggled")

    if st.button("🏠 Home", key="home", use_container_width=True):
        if controller.home():
            st.success("Home pressed")
