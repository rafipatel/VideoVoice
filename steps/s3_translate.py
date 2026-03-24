"""
Step 4: Translate segment texts using Pollinations chat completions API
(OpenAI-compatible endpoint, no extra API key needed beyond POLLEN_API_KEY).
"""
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

POLLINATIONS_BASE = "https://gen.pollinations.ai/v1"
MODEL = "openai"  # Pollinations routes this to GPT-4o


def _build_client() -> OpenAI:
    api_key = os.getenv("POLLEN_API_KEY", "pollinations")
    return OpenAI(base_url=POLLINATIONS_BASE, api_key=api_key)


def translate(segments: list[dict], target_language: str) -> list[dict]:
    """
    Translate the text of each segment into target_language.

    Args:
        segments: List of {start, end, text} dicts.
        target_language: Full language name, e.g. "Spanish", "French", "Hindi".

    Returns:
        Same list with 'translated_text' added to each segment.
    """
    if not segments:
        return segments

    print(f"[s3] Translating {len(segments)} segments → {target_language}...")

    # Build single-shot batch: send all texts as a numbered JSON list
    texts = [s["text"] for s in segments]
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts))

    system_prompt = (
        f"You are a professional subtitle translator. "
        f"Translate the following numbered lines into {target_language}. "
        f"Preserve the numbering exactly. "
        f"Return ONLY a JSON array of translated strings, in order, no extra text. "
        f"Example: [\"translated line 1\", \"translated line 2\"]"
    )

    client = _build_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": numbered},
        ],
        temperature=0.2,
    )

    raw = response.choices[0].message.content.strip()

    # Parse JSON array
    try:
        translated_list = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract array if there's surrounding text
        import re
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            translated_list = json.loads(match.group())
        else:
            raise ValueError(f"Could not parse translation response:\n{raw}")

    if len(translated_list) != len(segments):
        raise ValueError(
            f"Translation returned {len(translated_list)} items but expected {len(segments)}"
        )

    result = []
    for seg, translated_text in zip(segments, translated_list):
        result.append({**seg, "translated_text": translated_text})

    print(f"[s3] Translation complete ✓")
    return result
