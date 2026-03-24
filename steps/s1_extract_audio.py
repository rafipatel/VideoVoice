"""
Step 1-2: Extract audio track from input video.
Outputs a 16 kHz mono WAV suitable for Whisper + Chatterbox.
"""
import subprocess
from pathlib import Path


def extract_audio(video_path: str, output_path: str = "tmp/extracted_audio.wav") -> str:
    """
    Extract audio from video using ffmpeg.

    Args:
        video_path: Path to the input video file.
        output_path: Where to save the extracted audio (WAV).

    Returns:
        Absolute path to the extracted audio file.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",                  # no video
        "-acodec", "pcm_s16le", # PCM 16-bit
        "-ar", "16000",         # 16 kHz (Whisper standard)
        "-ac", "1",             # mono
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed:\n{result.stderr}")

    print(f"[s1] Audio extracted → {output_path}")
    return output_path
