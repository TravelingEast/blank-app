import io
import os
import subprocess
import sys
import tempfile
import zipfile

import streamlit as st

st.set_page_config(page_title="TikTok Video Downloader", page_icon="🎵", layout="centered")

st.title("TikTok Video Downloader")
st.write("Download all videos from any public TikTok profile, or your own account using browser cookies.")

if "zip_data" not in st.session_state:
    st.session_state.zip_data = None
if "video_count" not in st.session_state:
    st.session_state.video_count = 0
if "zip_filename" not in st.session_state:
    st.session_state.zip_filename = "tiktok_videos.zip"

# --- Input ---
username_input = st.text_input(
    "TikTok Username or Profile URL",
    placeholder="@username  or  https://www.tiktok.com/@username",
)

with st.expander("Authentication (required for private videos / your own account)"):
    st.markdown(
        "To download **private videos** or all videos from your own account, "
        "provide your TikTok session cookies.\n\n"
        "**How to get cookies:**\n"
        "1. Install the browser extension *Get cookies.txt LOCALLY*\n"
        "2. Log in to TikTok in your browser\n"
        "3. Click the extension and export cookies in **Netscape format**\n"
        "4. Paste the contents below"
    )
    cookies_text = st.text_area("Cookies (Netscape format)", height=120, placeholder="# Netscape HTTP Cookie File\n...")

with st.expander("Download Options"):
    col1, col2 = st.columns(2)
    with col1:
        quality = st.selectbox(
            "Video Quality",
            ["best", "bestvideo[height<=1080]+bestaudio", "bestvideo[height<=720]+bestaudio", "worst"],
            format_func=lambda x: {
                "best": "Best available",
                "bestvideo[height<=1080]+bestaudio": "Up to 1080p",
                "bestvideo[height<=720]+bestaudio": "Up to 720p",
                "worst": "Smallest file size",
            }[x],
        )
    with col2:
        limit = st.number_input("Max videos (0 = all)", min_value=0, value=0, step=10)
    write_metadata = st.checkbox("Embed metadata (title, description, thumbnail)", value=True)

# --- Download ---
if st.button("Download All Videos", type="primary", use_container_width=True):
    st.session_state.zip_data = None

    raw = username_input.strip()
    if not raw:
        st.error("Please enter a TikTok username or profile URL.")
        st.stop()

    if raw.startswith("http"):
        profile_url = raw
        slug = raw.rstrip("/").split("/")[-1].lstrip("@") or "tiktok"
    else:
        slug = raw.lstrip("@")
        profile_url = f"https://www.tiktok.com/@{slug}"

    st.info(f"Fetching videos from: **{profile_url}**")

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--newline",
            "--no-warnings",
            "-f", quality,
            "-o", os.path.join(tmpdir, "%(uploader)s_%(title).50s_%(id)s.%(ext)s"),
        ]

        if write_metadata:
            cmd += ["--embed-thumbnail", "--add-metadata"]

        if limit > 0:
            cmd += ["--playlist-end", str(limit)]

        cookies_file = None
        if cookies_text.strip():
            cookies_file = os.path.join(tmpdir, "cookies.txt")
            with open(cookies_file, "w") as f:
                f.write(cookies_text.strip())
            cmd += ["--cookies", cookies_file]

        cmd.append(profile_url)

        log_area = st.empty()
        log_lines: list[str] = []

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            assert process.stdout is not None
            for line in process.stdout:
                line = line.rstrip()
                if line:
                    log_lines.append(line)
                    log_area.code("\n".join(log_lines[-20:]), language=None)

            process.wait()
        except FileNotFoundError:
            st.error("yt-dlp not found. Run: `pip3 install yt-dlp`")
            st.stop()

        downloaded = [
            f
            for f in os.listdir(tmpdir)
            if os.path.isfile(os.path.join(tmpdir, f)) and f != "cookies.txt"
        ]

        if not downloaded:
            st.warning(
                "No videos were downloaded. Possible reasons:\n"
                "- The account is private (add cookies above)\n"
                "- The username is incorrect\n"
                "- TikTok rate-limited the request"
            )
        else:
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for fname in downloaded:
                    zf.write(os.path.join(tmpdir, fname), fname)

            st.session_state.zip_data = buf.getvalue()
            st.session_state.video_count = len(downloaded)
            st.session_state.zip_filename = f"tiktok_{slug}_videos.zip"
            st.success(f"Downloaded **{len(downloaded)}** video(s) successfully!")

# --- Download button (persists across reruns) ---
if st.session_state.zip_data:
    st.download_button(
        label=f"Save {st.session_state.video_count} Videos as ZIP",
        data=st.session_state.zip_data,
        file_name=st.session_state.zip_filename,
        mime="application/zip",
        use_container_width=True,
    )

st.divider()
st.caption(
    "Uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) under the hood. "
    "Only download content you own or have permission to download."
)
