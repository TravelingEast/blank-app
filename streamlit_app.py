import streamlit as st
import requests
import socket
from typing import Optional, Dict, List
import json

st.set_page_config(page_title="Samsung TV Controller", layout="wide")

st.title("📺 Samsung TV Controller")
st.markdown("Control your Samsung TV's volume and input from your browser")

class SamsungTVController:
    def __init__(self, ip: str, port: int = 8002):
        self.ip = ip
        self.port = port
        self.base_url = f"http://{ip}:{port}"
        self.session = requests.Session()

    def send_command(self, command: str, payload: Optional[Dict] = None) -> bool:
        try:
            url = f"{self.base_url}/api/v2/{command}"
            headers = {"Content-Type": "application/json"}
            response = self.session.post(url, json=payload or {}, headers=headers, timeout=2)
            return response.status_code in [200, 201]
        except Exception as e:
            st.error(f"Failed to send command: {str(e)}")
            return False

    def volume_up(self) -> bool:
        return self.send_command("keypad/hold/KEY_VOL_UP", {})

    def volume_down(self) -> bool:
        return self.send_command("keypad/hold/KEY_VOL_DOWN", {})

    def set_volume(self, level: int) -> bool:
        return self.send_command("keypad/hold/KEY_VOL_DOWN", {})

    def get_volume(self) -> Optional[int]:
        try:
            response = self.session.get(f"{self.base_url}/api/v2/channels/currentChannel", timeout=2)
            if response.status_code == 200:
                data = response.json()
                return data.get("volumeLevel")
        except:
            pass
        return None

    def get_inputs(self) -> List[Dict]:
        try:
            response = self.session.get(f"{self.base_url}/api/v2/channels", timeout=2)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return []

    def change_input(self, input_id: str) -> bool:
        return self.send_command(f"channels/{input_id}", {})

    def is_alive(self) -> bool:
        try:
            response = self.session.get(f"{self.base_url}/api/v2/", timeout=1)
            return response.status_code == 200
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
        if st.button("🔄 Get Available Inputs", key="get_inputs"):
            try:
                inputs = controller.get_inputs()
                if inputs:
                    st.write("Available inputs:")
                    for inp in inputs[:10]:  # Limit display
                        col_name, col_btn = st.columns([3, 1])
                        with col_name:
                            st.write(inp.get("name", "Unknown"))
                        with col_btn:
                            if st.button("Switch", key=f"input_{inp.get('id', '')}"):
                                if controller.change_input(inp.get("id", "")):
                                    st.success(f"Switched to {inp.get('name', 'input')}")
                                else:
                                    st.error("Failed to switch input")
                else:
                    st.info("No inputs found or TV unreachable")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    st.divider()

    # Quick actions
    st.subheader("⚡ Quick Commands")
    quick_col1, quick_col2, quick_col3 = st.columns(3)

    with quick_col1:
        if st.button("Power Off", key="power_off"):
            if controller.send_command("keypad/hold/KEY_POWER", {}):
                st.success("Power command sent")
            else:
                st.error("Failed to send power command")

    with quick_col2:
        if st.button("Mute", key="mute"):
            if controller.send_command("keypad/hold/KEY_MUTE", {}):
                st.success("Mute toggled")
            else:
                st.error("Failed to mute")

    with quick_col3:
        if st.button("Home", key="home"):
            if controller.send_command("keypad/hold/KEY_HOME", {}):
                st.success("Home pressed")
            else:
                st.error("Failed to go home")
