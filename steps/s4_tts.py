# """
# Step 5: Voice clone + TTS using Resemble AI Chatterbox.

# Clones the speaker's voice from the original audio and synthesises
# each translated segment. Works on Apple Silicon via MPS/CPU.
# """
# import os
# import torch
# import torchaudio
# from pathlib import Path
# from tqdm import tqdm


# def _get_device() -> str:
#     if torch.backends.mps.is_available():
#         return "mps"
#     elif torch.cuda.is_available():
#         return "cuda"
#     return "cpu"


# def synthesise_segments(
#     segments: list[dict],
#     reference_audio_path: str,
#     output_dir: str = "tmp/tts_segments",
# ) -> list[dict]:
#     """
#     Synthesise translated text for each segment using voice cloned from reference audio.

#     Args:
#         segments: List of {start, end, text, translated_text} dicts.
#         reference_audio_path: Path to the original extracted audio (voice reference).
#         output_dir: Directory to save per-segment WAV files.

#     Returns:
#         Same segments list with 'tts_path' added to each.
#     """
#     from chatterbox.tts import ChatterboxTTS

#     Path(output_dir).mkdir(parents=True, exist_ok=True)
#     device = _get_device()
#     print(f"[s4] Loading Chatterbox TTS on device: {device}")

#     model = ChatterboxTTS.from_pretrained(device=device)

#     results = []
#     for i, seg in enumerate(tqdm(segments, desc="[s4] Synthesising")):
#         text = seg.get("translated_text", seg["text"])
#         out_path = os.path.join(output_dir, f"seg_{i:04d}.wav")

#         wav = model.generate(
#             text,
#             audio_prompt_path=reference_audio_path,
#         )

#         torchaudio.save(out_path, wav, model.sr)
#         results.append({**seg, "tts_path": out_path})

#     print(f"[s4] TTS complete — {len(results)} segments synthesised ✓")
#     return results




"""
Step 5: Voice clone + TTS using Resemble AI Chatterbox Multilingual.

Clones the speaker's voice from the original audio and synthesises
each translated segment. Works on Apple Silicon via MPS/CPU.
"""
import os
import torch
import torchaudio
from pathlib import Path
from tqdm import tqdm


def _get_device() -> str:
    if torch.backends.mps.is_available():
        return "mps"
    elif torch.cuda.is_available():
        return "cuda"
    return "cpu"


def synthesise_segments(
    segments: list[dict],
    reference_audio_path: str,
    language_id: str = "en",
    output_dir: str = "tmp/tts_segments",
) -> list[dict]:
    """
    Synthesise translated text for each segment using voice cloned from reference audio.

    Args:
        segments: List of {start, end, text, translated_text} dicts.
        reference_audio_path: Path to the original extracted audio (voice reference).
        language_id: Language code for synthesis (e.g. "en", "fr", "de", "es",
                     "it", "pt", "hi", "ja", "zh", "ko", "ar" …).
        output_dir: Directory to save per-segment WAV files.

    Returns:
        Same segments list with 'tts_path' added to each.
    """
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    device = _get_device()
    print(f"[s5] Loading Chatterbox Multilingual TTS on device: {device}")

    model = ChatterboxMultilingualTTS.from_pretrained(device)

    results = []
    for i, seg in enumerate(tqdm(segments, desc="[s4] Synthesising")):
        text = seg.get("translated_text", seg["text"])
        out_path = os.path.join(output_dir, f"seg_{i:04d}.wav")

        orig_dur = seg["end"] - seg["start"]
        max_tokens = min(1000, max(150, int(orig_dur * 75 * 1.5)))

        wav = model.generate(
            text[:300],
            language_id=language_id,
            audio_prompt_path=reference_audio_path,
            exaggeration=0.5,
            temperature=0.8,
            cfg_weight=0.5,
        )

        torchaudio.save(out_path, wav, model.sr)
        results.append({**seg, "tts_path": out_path})

    print(f"[s5] TTS complete — {len(results)} segments synthesised ✓")
    return results