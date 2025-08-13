import streamlit as st
import subprocess
import os
import tempfile
from pathlib import Path

st.set_page_config(page_title="🎬 Live Video Speed Controller", page_icon="⚡", layout="centered")
st.title("⚡ Live Video Speed Controller")
st.markdown("🎛 Drag the slider or type a value. Live preview updates as you adjust.")

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
uploaded_file = st.file_uploader(
    "📤 Upload video", 
    type=["mp4", "mov", "avi", "mkv", "webm"]
)

# ==== Speed Controls ====
min_speed, max_speed = 0.1, 8.0

col1, col2 = st.columns(2)
with col1:
    speed_slider = st.slider("Speed factor (slider)", min_speed, max_speed, 1.0, 0.05)
with col2:
    speed_manual = st.number_input("Speed factor (manual)", min_value=min_speed, max_value=max_speed, value=speed_slider, step=0.01, format="%.2f")

# Decide which one to use: manual takes precedence if changed
if abs(speed_manual - speed_slider) > 1e-6:
    speed_factor = speed_manual
else:
    speed_factor = speed_slider

# ==== Process whenever file uploaded and speed changes ====
if uploaded_file and speed_factor > 0:
    with st.spinner(f"⏳ Processing at {speed_factor:.2f}x speed..."):
        tmp_dir = tempfile.mkdtemp()
        input_path = os.path.join(tmp_dir, uploaded_file.name)
        ext = Path(uploaded_file.name).suffix
        output_path = os.path.join(tmp_dir, f"output{ext}")

        # Save uploaded file
        with open(input_path, "wb") as f:
            f.write(uploaded_file.read())

        # Build FFmpeg filters
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
            st.error("❌ FFmpeg failed to process the video.")
            st.code(process.stderr)
        else:
            st.success(f"✅ Done! Speed: {speed_factor:.2f}x")
            st.video(output_path)
            with open(output_path, "rb") as out_file:
                st.download_button("📥 Download this version", out_file, file_name=f"processed{ext}")
