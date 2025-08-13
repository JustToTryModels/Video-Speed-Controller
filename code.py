import streamlit as st
import subprocess
import os
import tempfile
from pathlib import Path

st.set_page_config(page_title="🎬 Video Speed Live Preview", page_icon="⚡", layout="centered")
st.title("🎬 Video Speed Controller – Live Preview Edition")
st.markdown("🎛 Slide the speed control & preview updates instantly after processing.")

# ==== Helper: atempo chaining ====
def atempo_chain(sf):
    tempos = []
    while sf > 2.0:
        tempos.append("atempo=2.0")
        sf /= 2.0
    while sf < 0.5:
        tempos.append("atempo=0.5")
        sf *= 2.0
    tempos.append(f"atempo={sf}")
    return ",".join(tempos)

# ==== File Upload ====
uploaded_file = st.file_uploader("📤 Upload video", type=["mp4", "mov", "avi", "mkv", "webm"])
speed_factor = st.slider("Speed factor", 0.25, 4.0, 1.0, 0.05)

# ==== Process live when slider changes ====
if uploaded_file and speed_factor > 0:
    with st.spinner("Processing video... hang tight!"):
        tmp_dir = tempfile.mkdtemp()
        input_path = os.path.join(tmp_dir, uploaded_file.name)
        ext = Path(uploaded_file.name).suffix
        output_path = os.path.join(tmp_dir, f"output{ext}")

        # Save uploaded file
        with open(input_path, "wb") as f:
            f.write(uploaded_file.read())

        # Build FFmpeg command
        atempo_filters = atempo_chain(speed_factor)
        ffmpeg_cmd = [
            "ffmpeg", "-i", input_path,
            "-vf", f"setpts={1/speed_factor}*PTS",
            "-af", atempo_filters,
            "-c:v", "libx264", "-crf", "18", "-preset", "ultrafast",
            "-c:a", "aac", "-b:a", "192k",
            "-y", output_path
        ]

        # Run FFmpeg
        process = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if process.returncode != 0:
            st.error("❌ FFmpeg failed!")
            st.code(process.stderr)
        else:
            st.video(output_path)
            with open(output_path, "rb") as out_file:
                st.download_button("📥 Download this version", out_file, file_name=f"processed{ext}")
