"""
Step 3: Transcribe audio with timestamps.

Primary:  Pollinations Whisper Large V3 API (verbose_json)
Fallback: mlx-whisper medium (M3 Metal-accelerated, local)
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

POLLINATIONS_URL = "https://gen.pollinations.ai/v1/audio/transcriptions"
MLX_MODEL = "mlx-community/whisper-medium-mlx"


def _segments_from_pollinations(audio_path: str, language: str) -> list[dict]:
    """Call Pollinations Whisper API, return list of {start, end, text} segments."""
    api_key = os.getenv("POLLEN_API_KEY_SECONDARY") or os.getenv("POLLEN_API_KEY", "")
    headers = {"Authorization": f"Bearer {api_key}"}

    with open(audio_path, "rb") as f:
        files = {"file": (os.path.basename(audio_path), f, "audio/wav")}
        data = {
            "model": "whisper-large-v3",
            "language": language,
            "response_format": "verbose_json",
            "temperature": 0,
        }
        response = requests.post(POLLINATIONS_URL, headers=headers, files=files, data=data, timeout=120)

    response.raise_for_status()
    result = response.json()

    segments = result.get("segments", [])
    return [{"start": s["start"], "end": s["end"], "text": s["text"].strip()} for s in segments]


def _segments_from_mlx(audio_path: str, language: str) -> list[dict]:
    """Fallback: run mlx-whisper locally on M3 Metal."""
    print("[s2] Falling back to mlx-whisper (local M3)...")
    try:
        import mlx_whisper
    except ImportError:
        raise ImportError("mlx-whisper is not installed. Run: pip install mlx-whisper")

    result = mlx_whisper.transcribe(
        audio_path,
        path_or_hf_repo=MLX_MODEL,
        language=language if language != "auto" else None,
        word_timestamps=True,
    )

    segments = result.get("segments", [])
    return [{"start": s["start"], "end": s["end"], "text": s["text"].strip()} for s in segments]


def transcribe(audio_path: str, language: str = "en") -> list[dict]:
    """
    Transcribe audio and return segments with timestamps.

    Args:
        audio_path: Path to WAV file.
        language: ISO-639-1 language code of the source audio (e.g. "en").

    Returns:
        List of dicts: [{start: float, end: float, text: str}, ...]
    """
    print(f"[s2] Transcribing {audio_path} (lang={language})...")

    try:
        segments = _segments_from_pollinations(audio_path, language)
        if segments:
            print(f"[s2] Pollinations returned {len(segments)} segments ✓")
            return segments
        else:
            print("[s2] Pollinations returned no segments — using mlx-whisper fallback.")
    except Exception as e:
        print(f"[s2] Pollinations error ({e}) — using mlx-whisper fallback.")

    segments = _segments_from_mlx(audio_path, language)
    print(f"[s2] mlx-whisper returned {len(segments)} segments ✓")
    return segments
