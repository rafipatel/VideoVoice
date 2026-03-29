"""
Step 6: Audio sync — match synthesised segment durations to original timestamps.

For each segment:
  - Too long  → speed up using ffmpeg atempo filter
  - Too short → pad with silence at the end
Then stitch all segments into a single final audio track.
"""
import os
import subprocess
import struct
import wave
from pathlib import Path


def _get_wav_duration(wav_path: str) -> float:
    with wave.open(wav_path, 'r') as f:
        frames = f.getnframes()
        rate = f.getframerate()
        return frames / float(rate)


def _speedup_audio(input_path: str, output_path: str, factor: float) -> None:
    """Speed up/slow down audio by factor using ffmpeg atempo (supports 0.5–100x via chaining)."""
    # atempo supports 0.5 to 2.0, chain filters for larger factors
    filters = []
    remaining = factor
    while remaining > 2.0:
        filters.append("atempo=2.0")
        remaining /= 2.0
    while remaining < 0.5:
        filters.append("atempo=0.5")
        remaining /= 0.5
    filters.append(f"atempo={remaining:.4f}")
    filter_str = ",".join(filters)

    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-filter:a", filter_str,
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg atempo failed:\n{result.stderr}")


def _pad_silence(input_path: str, output_path: str, target_duration: float) -> None:
    """Pad audio with silence to reach target_duration seconds."""
    current = _get_wav_duration(input_path)
    pad_seconds = max(0, target_duration - current)

    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-af", f"apad=pad_dur={pad_seconds:.4f}",
        "-t", str(target_duration),
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg apad failed:\n{result.stderr}")


def _generate_silence(output_path: str, duration: float, sample_rate: int = 16000) -> None:
    """Generate a silent WAV file of given duration."""
    num_samples = int(duration * sample_rate)
    with wave.open(output_path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)  # 16-bit
        f.setframerate(sample_rate)
        f.writeframes(b"\x00\x00" * num_samples)


def sync_and_stitch(
    segments: list[dict],
    output_path: str = "tmp/final_audio.wav",
    synced_dir: str = "tmp/tts_synced",
    max_speed: float = 1.8,
) -> str:
    """
    Sync each TTS segment to its original timestamp window and stitch into a single WAV.

    Args:
        segments: List of dicts with {start, end, tts_path}.
        output_path: Where to write the final stitched audio.
        synced_dir: Temp directory for per-segment synced WAVs.
        max_speed: Maximum allowed speedup factor (default 1.8x to preserve naturalness).

    Returns:
        Path to the final stitched audio WAV.
    """
    Path(synced_dir).mkdir(parents=True, exist_ok=True)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Build a timeline: we'll fill gaps with silence and place each synced segment
    # Final audio length = end time of last segment
    total_duration = segments[-1]["end"] if segments else 0

    # Collect per-position synced wavs in order
    silence_counter = [0]
    concat_list_path = "tmp/concat_list.txt"
    concat_entries = []

    prev_end = 0.0
    for i, seg in enumerate(segments):
        start = seg["start"]
        end = seg["end"]
        target_duration = end - start
        tts_path = seg["tts_path"]

        # Fill gap before this segment with silence
        gap = start - prev_end
        if gap > 0.01:
            sil_path = os.path.join(synced_dir, f"silence_{i:04d}.wav")
            _generate_silence(sil_path, gap)
            concat_entries.append(sil_path)

        # Sync the TTS segment
        tts_duration = _get_wav_duration(tts_path)
        synced_path = os.path.join(synced_dir, f"synced_{i:04d}.wav")

        if tts_duration > target_duration * 1.02:
            speed_factor = min(tts_duration / target_duration, max_speed)
            print(f"[s5] Seg {i}: speeding up ×{speed_factor:.2f}")
            _speedup_audio(tts_path, synced_path, speed_factor)
        elif tts_duration < target_duration * 0.98:
            print(f"[s5] Seg {i}: padding {target_duration - tts_duration:.2f}s silence")
            _pad_silence(tts_path, synced_path, target_duration)
        else:
            import shutil
            shutil.copy(tts_path, synced_path)

        concat_entries.append(synced_path)
        prev_end = end

    # Write concat list for ffmpeg
    with open(concat_list_path, "w") as f:
        for entry in concat_entries:
            abs_entry = os.path.abspath(entry)
            f.write(f"file '{abs_entry}'\n")

    # Concatenate all segments
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg concat failed:\n{result.stderr}")

    print(f"[s5] Audio sync complete → {output_path} ✓")
    return output_path
