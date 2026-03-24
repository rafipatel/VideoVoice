"""
pipeline.py — Core pipeline: CLI entrypoint + importable run_pipeline() for Gradio.

Usage:
    python pipeline.py --input data/test_video_3.mp4 --target-lang Spanish
"""
import argparse
import os
import shutil
from pathlib import Path
from typing import Generator

from steps.s1_extract_audio import extract_audio
from steps.s2_transcribe import transcribe
from steps.s3_translate import translate
from steps.s4_tts import synthesise_segments
from steps.s5_sync import sync_and_stitch
from steps.s6_merge import merge_audio_video

LANGUAGE_CODES = {
    "Spanish": "es",
    "French": "fr",
    "Hindi": "hi",
    "German": "de",
    "Portuguese": "pt",
    "Italian": "it",
    "Japanese": "ja",
    "Chinese": "zh",
    "Arabic": "ar",
    "Korean": "ko",
}


def run_pipeline(
    video_path: str,
    target_language: str = "Spanish",
    source_language: str = "en",
    output_path: str | None = None,
) -> Generator[str, None, str]:
    """
    Run the full translation pipeline, yielding progress messages.

    Args:
        video_path: Path to the input video file.
        target_language: Target language name (e.g. "Spanish").
        source_language: ISO-639-1 code of the source language (default "en").
        output_path: Where to save the output video. Auto-generated if None.

    Yields:
        str: Progress messages for each step.

    Returns:
        str: Path to the translated output video.
    """
    # Prepare output path
    if output_path is None:
        stem = Path(video_path).stem
        output_path = f"output_{stem}_{target_language.lower()}.mp4"

    # Clean tmp dir
    shutil.rmtree("tmp", ignore_errors=True)
    os.makedirs("tmp", exist_ok=True)

    yield f"🎬 Starting pipeline: {video_path} → {target_language}\n"

    # Step 1: Extract audio
    yield "🔊 Step 1/6: Extracting audio...\n"
    audio_path = extract_audio(video_path, "tmp/extracted_audio.wav")
    yield f"   ✓ Audio extracted: {audio_path}\n"

    # Step 2: Transcribe
    yield "📝 Step 2/6: Transcribing (Pollinations Whisper / mlx-whisper)...\n"
    segments = transcribe(audio_path, language=source_language)
    yield f"   ✓ {len(segments)} segments transcribed\n"
    for s in segments:
        yield f"   [{s['start']:.1f}s–{s['end']:.1f}s] {s['text']}\n"

    # Step 3: Translate
    yield f"🌍 Step 3/6: Translating to {target_language}...\n"
    segments = translate(segments, target_language)
    yield f"   ✓ Translation complete\n"
    for s in segments:
        yield f"   → {s['translated_text']}\n"

    # Step 4: TTS + voice cloning
    yield "🗣️ Step 4/6: Synthesising speech (Chatterbox Multilingual voice clone)...\n"
    target_lang_code = LANGUAGE_CODES.get(target_language, "es")
    segments = synthesise_segments(segments, audio_path, language_id=target_lang_code, output_dir="tmp/tts_segments")
    yield f"   ✓ {len(segments)} segments synthesised\n"

    # Step 5: Sync
    yield "⏱️ Step 5/6: Syncing audio to original timestamps...\n"
    final_audio = sync_and_stitch(segments, "tmp/final_audio.wav", "tmp/tts_synced")
    yield f"   ✓ Audio synced: {final_audio}\n"

    # Step 6: Merge
    yield "🎞️ Step 6/6: Merging translated audio into video...\n"
    result = merge_audio_video(video_path, final_audio, output_path)
    yield f"\n✅ Done! Output saved to: {result}\n"

    return result


def _collect_output(gen: Generator) -> tuple[list[str], str]:
    """Collect all yields and the return value from the generator."""
    messages = []
    output_path = None
    try:
        while True:
            msg = next(gen)
            messages.append(msg)
            print(msg, end="", flush=True)
    except StopIteration as e:
        output_path = e.value
    return messages, output_path


def main():
    parser = argparse.ArgumentParser(description="Video Translation Pipeline")
    parser.add_argument("--input", required=True, help="Input video path")
    parser.add_argument(
        "--target-lang",
        default="Spanish",
        choices=list(LANGUAGE_CODES.keys()),
        help="Target language (default: Spanish)",
    )
    parser.add_argument(
        "--source-lang",
        default="en",
        help="Source language ISO-639-1 code (default: en)",
    )
    parser.add_argument("--output", default=None, help="Output video path")
    args = parser.parse_args()

    gen = run_pipeline(
        video_path=args.input,
        target_language=args.target_lang,
        source_language=args.source_lang,
        output_path=args.output,
    )
    _, output = _collect_output(gen)
    print(f"\nFinal output: {output}")


if __name__ == "__main__":
    main()
