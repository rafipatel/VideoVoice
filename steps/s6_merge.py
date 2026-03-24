"""
Step 7: Merge translated audio back into the original video.
"""
import subprocess
from pathlib import Path


def merge_audio_video(
    video_path: str,
    audio_path: str,
    output_path: str = "output_translated.mp4",
) -> str:
    """
    Replace the audio track of video_path with audio_path.

    Args:
        video_path: Original video file.
        audio_path: New audio WAV file (translated + synced).
        output_path: Output video file path.

    Returns:
        Path to the output video.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,        # original video (video+audio tracks)
        "-i", audio_path,        # new audio
        "-map", "0:v:0",         # take video from input 0
        "-map", "1:a:0",         # take audio from input 1
        "-c:v", "copy",          # copy video stream (no re-encode, fast)
        "-c:a", "aac",           # encode audio as AAC for MP4
        "-shortest",             # trim to shortest stream
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg merge failed:\n{result.stderr}")

    print(f"[s6] Final video → {output_path} ✓")
    return output_path
