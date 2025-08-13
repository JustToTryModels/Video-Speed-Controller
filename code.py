import streamlit as st
import subprocess
import os
import tempfile
from pathlib import Path

st.set_page_config(page_title="🎬 Live Video Speed Controller", page_icon="⚡", layout="centered")
st.title("⚡ Live Video Speed Controller")
st.markdown(
    "🎛 Upload a video, adjust the speed (0.1× to 8×), "
    "and preview/download your processed file with the speed tagged in the filename."
)

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
    speed_manual = st.number_input(
        "Speed factor (manual)",
        min_value=min_speed, max_value=max_speed,
        value=speed_slider, step=0.01, format="%.2f"
    )

# Determine which input to use
if abs(speed_manual - speed_slider) > 1e-6:
    speed_factor = speed_manual
else:
    speed_factor = speed_slider

# ==== Process the file and show live preview ====
if uploaded_file and speed_factor > 0:
    with st.spinner(f"⏳ Processing at {speed_factor:.2f}× speed..."):
        tmp_dir = tempfile.mkdtemp()
        
        # Original file info
        original_filename = uploaded_file.name
        input_path = os.path.join(tmp_dir, original_filename)
        base_name = Path(original_filename).stem
        ext = Path(original_filename).suffix
        
        # Output filename: original + .<speed>x + extension
        safe_speed_str = f"{speed_factor:.2f}".rstrip("0").rstrip(".")  # cleaner string
        output_filename = f"{base_name}.{safe_speed_str}x{ext}"
        output_path = os.path.join(tmp_dir, output_filename)

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
            st.success(f"✅ Done! Speed: {speed_factor:.2f}×")
            st.video(output_path)

            # Inject CSS to make the download button red
            st.markdown(
                """
                <style>
                div.stDownloadButton > button {
                    background-color: red !important;
                    color: white !important;
                    border-color: darkred !important;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

            with open(output_path, "rb") as out_file:
                st.download_button(
                    "📥 Download Processed Video", 
                    out_file, 
                    file_name=output_filename
                ) 
